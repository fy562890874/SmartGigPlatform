from ..models.favorite import Favorite, FavoriteTypeEnum
from ..models.job import Job
from ..models.user import User
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, BusinessException, InvalidUsageException
from datetime import datetime

class FavoriteService:
    def add_item_to_favorites(self, user_id, favorite_data):
        """
        添加项目到收藏
        :param user_id: 用户ID
        :param favorite_data: 收藏数据，包含favorite_type, target_id
        :return: 创建的Favorite对象，附带target_details
        """
        from flask import current_app
        
        # 校验收藏类型
        favorite_type_str = favorite_data.get('favorite_type')
        if not favorite_type_str or favorite_type_str not in [ft.value for ft in FavoriteTypeEnum]:
            raise InvalidUsageException(message="无效的收藏类型", error_code=40001)
        
        favorite_type = FavoriteTypeEnum(favorite_type_str)
        target_id = favorite_data.get('target_id')
        
        if not target_id:
            raise InvalidUsageException(message="未提供收藏目标ID", error_code=40002)
        
        # 根据收藏类型校验目标的有效性
        target = None
        target_details = None
        
        if favorite_type == FavoriteTypeEnum.job:
            # 校验工作存在
            target = Job.query.get(target_id)
            if target:
                target_details = {
                    "type": "job",
                    "id": target.id,
                    "title": target.title
                }
        
        elif favorite_type in [FavoriteTypeEnum.freelancer, FavoriteTypeEnum.employer]:
            # 校验用户存在且角色匹配
            target = User.query.get(target_id)
            
            if target:
                # 检查用户角色是否与收藏类型匹配
                if favorite_type == FavoriteTypeEnum.freelancer:
                    # 检查是否有零工角色
                    has_role = False
                    if hasattr(target, 'available_roles'):
                        if isinstance(target.available_roles, list) and 'freelancer' in target.available_roles:
                            has_role = True
                        elif isinstance(target.available_roles, str) and 'freelancer' in target.available_roles:
                            has_role = True
                    
                    if not has_role and getattr(target, 'current_role', '') != 'freelancer':
                        target = None
                    else:
                        nickname = getattr(target.freelancer_profile, 'nickname', '') if hasattr(target, 'freelancer_profile') else ''
                        target_details = {
                            "type": "freelancer",
                            "id": target.id,
                            "nickname": nickname or f"用户{target.id}"
                        }
                
                elif favorite_type == FavoriteTypeEnum.employer:
                    # 检查是否有雇主角色
                    has_role = False
                    if hasattr(target, 'available_roles'):
                        if isinstance(target.available_roles, list) and 'employer' in target.available_roles:
                            has_role = True
                        elif isinstance(target.available_roles, str) and 'employer' in target.available_roles:
                            has_role = True
                    
                    if not has_role and getattr(target, 'current_role', '') != 'employer':
                        target = None
                    else:
                        nickname = getattr(target.employer_profile, 'nickname', '') if hasattr(target, 'employer_profile') else ''
                        target_details = {
                            "type": "employer",
                            "id": target.id,
                            "nickname": nickname or f"用户{target.id}"
                        }
        
        if not target:
            raise NotFoundException(message="收藏目标不存在或类型不匹配", error_code=40404)
        
        # 检查是否已收藏
        existing = Favorite.query.filter_by(
            user_id=user_id,
            favorite_type=favorite_type,
            target_id=target_id
        ).first()
        
        if existing:
            raise BusinessException(message="已收藏该项目", status_code=409, error_code=40901)
        
        try:
            # 创建收藏记录
            new_favorite = Favorite(
                user_id=user_id,
                favorite_type=favorite_type,
                target_id=target_id
            )
            
            db.session.add(new_favorite)
            db.session.commit()
            
            # 在返回对象中附加target_details
            new_favorite.target_details = target_details
            
            return new_favorite
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"添加收藏失败: {str(e)}")
            raise BusinessException(message=f"添加收藏失败: {str(e)}", status_code=500, error_code=50001)

    def get_my_favorites_list(self, user_id, filters=None, page=1, per_page=10):
        """
        获取用户收藏列表
        :param user_id: 用户ID
        :param filters: 过滤条件，如favorite_type
        :param page: 页码
        :param per_page: 每页数量
        :return: 收藏列表和分页信息
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        # 构建基础查询
        query = Favorite.query.filter_by(user_id=user_id)
        
        # 应用过滤条件
        if 'favorite_type' in filters:
            try:
                favorite_type_value = filters['favorite_type']
                # 验证favorite_type是有效的枚举值
                if favorite_type_value in [ft.value for ft in FavoriteTypeEnum]:
                    query = query.filter(Favorite.favorite_type == favorite_type_value)
            except Exception as e:
                current_app.logger.warning(f"过滤收藏类型时出错: {str(e)}")
                # 无效的过滤条件，忽略
                pass
        
        # 按时间倒序排序
        query = query.order_by(Favorite.created_at.desc())
        
        # 执行分页
        paginated_favorites = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 为每个收藏项添加目标详情
        for favorite in paginated_favorites.items:
            favorite.target_details = self._get_target_details(favorite)
        
        return paginated_favorites

    def _get_target_details(self, favorite):
        """
        获取收藏目标的详细信息
        :param favorite: Favorite对象
        :return: 包含目标详情的字典
        """
        from flask import current_app
        
        target_details = {
            "type": favorite.favorite_type.value if hasattr(favorite.favorite_type, 'value') else str(favorite.favorite_type),
            "id": favorite.target_id
        }
        
        try:
            if favorite.favorite_type == FavoriteTypeEnum.job:
                job = Job.query.get(favorite.target_id)
                if job:
                    target_details.update({
                        "title": job.title,
                        "employer_nickname": getattr(job.employer.employer_profile, 'nickname', '') if hasattr(job, 'employer') and hasattr(job.employer, 'employer_profile') else f"雇主{job.employer_user_id}" if hasattr(job, 'employer_user_id') else "未知雇主"
                    })
            
            elif favorite.favorite_type == FavoriteTypeEnum.freelancer:
                user = User.query.get(favorite.target_id)
                if user and hasattr(user, 'freelancer_profile') and user.freelancer_profile:
                    target_details.update({
                        "nickname": user.freelancer_profile.nickname or f"用户{user.id}",
                        "avatar_url": user.freelancer_profile.avatar_url
                    })
            
            elif favorite.favorite_type == FavoriteTypeEnum.employer:
                user = User.query.get(favorite.target_id)
                if user and hasattr(user, 'employer_profile') and user.employer_profile:
                    target_details.update({
                        "nickname": user.employer_profile.nickname or f"用户{user.id}",
                        "avatar_url": user.employer_profile.avatar_url
                    })
        
        except Exception as e:
            current_app.logger.error(f"获取收藏目标详情时出错: {str(e)}")
            # 发生错误时返回基础信息
            pass
        
        return target_details

    def remove_favorite_item(self, user_id, favorite_id):
        """
        移除收藏项
        :param user_id: 用户ID
        :param favorite_id: 收藏ID
        :return: None
        """
        from flask import current_app
        
        # 查询收藏记录
        favorite_item = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()
        if not favorite_item:
            raise NotFoundException(message="收藏记录未找到或无权限删除", error_code=40404)
        
        try:
            # 删除收藏
            db.session.delete(favorite_item)
            db.session.commit()
            
            current_app.logger.info(f"已删除用户 {user_id} 的收藏记录 {favorite_id}")
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除收藏失败: {str(e)}")
            raise BusinessException(message=f"删除收藏失败: {str(e)}", status_code=500, error_code=50002)


# 服务实例
favorite_service = FavoriteService() 