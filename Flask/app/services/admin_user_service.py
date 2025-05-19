from ..models.user import User, UserStatusEnum, UserRoleEnum
from ..models.profile import FreelancerProfile, EmployerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from datetime import datetime

class AdminUserService:
    def get_all_users_paginated(self, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取用户列表并分页（管理员专用）
        :param filters: 过滤条件，例如status, role, q(搜索关键词)
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序字段
        :return: 分页后的用户列表
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        try:
            # 构建基础查询
            query = User.query
            
            # 预加载档案信息以优化性能
            query = query.options(
                joinedload(User.freelancer_profile),
                joinedload(User.employer_profile)
            )
            
            # 应用过滤条件
            if 'status' in filters and filters['status']:
                try:
                    status_enum = UserStatusEnum(filters['status'])
                    query = query.filter(User.status == status_enum)
                except ValueError:
                    # 无效的状态，忽略此过滤条件
                    current_app.logger.warning(f"管理员用户查询：无效的状态值 {filters['status']}")
                    pass
            
            if 'role' in filters and filters['role']:
                try:
                    role_enum = UserRoleEnum(filters['role'])
                    query = query.filter(User.current_role == role_enum)
                except ValueError:
                    # 无效的角色，忽略此过滤条件
                    current_app.logger.warning(f"管理员用户查询：无效的角色值 {filters['role']}")
                    pass
            
            # 关联用户档案表，用于搜索
            if 'q' in filters and filters['q']:
                search_term = f"%{filters['q']}%"
                query = query.outerjoin(User.freelancer_profile).outerjoin(User.employer_profile)
                
                # 构建OR条件进行模糊查询
                search_conditions = [
                    User.phone_number.ilike(search_term),
                    User.email.ilike(search_term),
                    FreelancerProfile.nickname.ilike(search_term),
                    FreelancerProfile.real_name.ilike(search_term),
                    EmployerProfile.nickname.ilike(search_term),
                    EmployerProfile.real_name.ilike(search_term),
                    EmployerProfile.company_name.ilike(search_term)
                ]
                
                query = query.filter(or_(*search_conditions))
            
            # 应用排序
            if sort_by == 'registered_at_desc':
                query = query.order_by(User.created_at.desc())
            elif sort_by == 'registered_at_asc':
                query = query.order_by(User.created_at.asc())
            elif sort_by == 'status':
                query = query.order_by(User.status.asc())
            else:
                # 默认按注册时间倒序
                query = query.order_by(User.created_at.desc())
            
            # 执行分页
            paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 记录日志
            current_app.logger.info(f"管理员查询用户列表，过滤条件: {filters}, 页码: {page}, 每页: {per_page}, 总数: {paginated_users.total}")
            
            return paginated_users
            
        except Exception as e:
            current_app.logger.error(f"管理员获取用户列表时出错: {str(e)}")
            raise BusinessException(message=f"获取用户列表失败: {str(e)}", status_code=500, error_code=50001)
    
    def update_user_status_by_admin(self, admin_user_id, user_uuid, new_status_data):
        """
        管理员更新用户状态
        :param admin_user_id: 管理员ID
        :param user_uuid: 用户UUID
        :param new_status_data: 状态数据，包含status, ban_reason(可选)
        :return: 更新后的用户对象
        """
        from flask import current_app
        
        # 验证状态值
        if 'status' not in new_status_data or not new_status_data['status']:
            raise InvalidUsageException(message="状态值不能为空", error_code=40001)
        
        try:
            # 验证状态是否为有效枚举值
            new_status = UserStatusEnum(new_status_data['status'])
        except ValueError:
            valid_statuses = [status.value for status in UserStatusEnum]
            raise InvalidUsageException(
                message=f"无效的状态值，有效值为: {', '.join(valid_statuses)}", 
                error_code=40002
            )
        
        try:
            # 查询用户
            user = User.query.filter_by(uuid=user_uuid).first()
            if not user:
                raise NotFoundException(message="用户不存在", error_code=40401)
            
            # 更新用户状态
            old_status = user.status
            user.status = new_status
            
            # 记录更新时间
            user.updated_at = datetime.utcnow()
            
            # 如果是封禁操作且有封禁原因，记录封禁原因
            ban_reason = None
            if new_status == UserStatusEnum.banned and 'ban_reason' in new_status_data:
                ban_reason = new_status_data['ban_reason']
                
                # 如果有审计日志或用户备注字段，在这里记录ban_reason
                # TODO: 例如 user.admin_notes = f"封禁原因: {ban_reason}"
                
                # 处理用户封禁后的附加操作，例如撤销工作、拒绝中的申请等
                # TODO: 调用相关服务处理封禁后效果
                
                # 将用户的当前令牌列入黑名单（如果系统支持）
                # TODO: 使当前会话失效
            
            # 提交更改
            db.session.commit()
            
            # 记录管理员操作日志
            status_change_msg = f"用户状态从 {old_status.value} 变更为 {new_status.value}"
            if ban_reason:
                status_change_msg += f"，原因: {ban_reason}"
            
            current_app.logger.info(f"管理员 {admin_user_id} 更新了用户 {user_uuid} 的状态: {status_change_msg}")
            
            # TODO: self._log_admin_action(admin_user_id, "update_user_status", user_uuid, status_change_msg)
            
            # 通知用户状态变更（如果状态变为封禁或恢复活跃）
            if old_status != new_status and new_status in [UserStatusEnum.banned, UserStatusEnum.active]:
                self._notify_user_status_change(user.id, new_status, ban_reason)
            
            return user
            
        except Exception as e:
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException):
                db.session.rollback()
                current_app.logger.error(f"更新用户状态时出错: {str(e)}")
                raise BusinessException(message=f"更新用户状态失败: {str(e)}", status_code=500, error_code=50002)
            raise e
    
    def _notify_user_status_change(self, user_id, status, reason=None):
        """
        通知用户状态变更
        :param user_id: 用户ID
        :param status: 新状态
        :param reason: 变更原因（可选）
        """
        from flask import current_app
        
        try:
            # 这里可以调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            notification_title = "账号状态变更通知"
            notification_content = f"您的账号状态已变更为 {status.value}"
            
            if status == UserStatusEnum.banned and reason:
                notification_content += f"，原因: {reason}"
            elif status == UserStatusEnum.active:
                notification_content += "，您现在可以正常使用平台功能"
            
            notification_data = {
                'notification_type': 'account_status_change',
                'title': notification_title,
                'content': notification_content
            }
            
            notification_service.create_notification(user_id, notification_data)
            current_app.logger.info(f"已向用户 {user_id} 发送状态变更通知")
            
        except Exception as e:
            current_app.logger.error(f"发送用户状态变更通知失败: {str(e)}")
            # 通知失败不阻断主流程


# 服务实例
admin_user_service = AdminUserService() 