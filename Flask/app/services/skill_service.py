from flask import current_app # Added for logging
from ..models.skill import Skill, FreelancerSkill
from ..models.user import User # To check if user is a freelancer
from ..models.profile import FreelancerProfile # Corrected import
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException

class SkillService:
    def get_all_skills(self, filters=None, page=1, per_page=20):
        """
        获取所有技能，支持筛选
        :param filters: 过滤条件，包含 q(搜索关键字)、category(分类)、is_hot(是否热门)
        :param page: 页码
        :param per_page: 每页数量
        :return: 分页后的技能列表
        """
        query = Skill.query
        if filters:
            # 按名称搜索
            if filters.get('q'):
                search_term = f"%{filters['q']}%"
                query = query.filter(Skill.name.ilike(search_term))
            
            # 按分类筛选
            if filters.get('category'):
                query = query.filter(Skill.category == filters['category'])
            
            # 按是否热门筛选
            if filters.get('is_hot') is not None:
                # 确保is_hot是布尔值
                is_hot_value = bool(filters['is_hot'])
                query = query.filter(Skill.is_hot == is_hot_value)
        
        # 排序：先按分类，再按名称
        query = query.order_by(Skill.category, Skill.name)
        
        # 分页
        paginated_skills = query.paginate(page=page, per_page=per_page, error_out=False)
        return paginated_skills

    def get_all_skill_categories(self):
        """获取所有唯一的技能分类列表"""
        try:
            # Query for distinct, non-null, non-empty categories
            categories_query = db.session.query(Skill.category).filter(
                Skill.category.isnot(None), 
                Skill.category != ''
            ).distinct().order_by(Skill.category)
            
            current_app.logger.info(f"获取所有技能分类，查询执行成功")
            
            # 将查询结果转换为列表
            categories = [item[0] for item in categories_query.all()]
            current_app.logger.info(f"成功获取 {len(categories)} 个技能分类")
            return categories
        except Exception as e:
            current_app.logger.error(f"获取所有技能分类失败: {str(e)}")
            # 包装异常，给客户端返回更友好的错误信息
            raise BusinessException(
                message="获取技能分类列表时发生错误", 
                internal_message=str(e),
                status_code=500, 
                error_code=50001
            )

    def get_skill_by_id(self, skill_id):
        skill = Skill.query.get(skill_id)
        if not skill:
            raise NotFoundException("技能不存在。")
        return skill

    def get_freelancer_skills(self, freelancer_user_id):
        user = User.query.get(freelancer_user_id)
        if not user or 'freelancer' not in user.available_roles:
            raise AuthorizationException("用户不是零工角色或不存在。", error_code=40302)
        
        # freelancer_skills = FreelancerSkill.query.filter_by(freelancer_user_id=freelancer_user_id).all()
        # To include skill details, we can join or load relationship
        freelancer_skills = FreelancerSkill.query.options(db.joinedload(FreelancerSkill.skill))\
                                             .filter_by(freelancer_user_id=freelancer_user_id).all()
        return freelancer_skills

    def add_skill_to_freelancer(self, freelancer_user_id, data):
        user = User.query.get(freelancer_user_id)
        if not user or 'freelancer' not in user.available_roles:
            raise AuthorizationException("仅零工用户可以添加技能。", error_code=40302)

        profile = FreelancerProfile.query.filter_by(user_id=freelancer_user_id).first()
        if not profile:
            raise NotFoundException("添加技能前，请先创建零工档案。")

        skill_id = data.get('skill_id')
        if not skill_id:
            raise InvalidUsageException("技能ID不能为空。")

        skill = self.get_skill_by_id(skill_id) # Ensures skill exists

        existing_fs = FreelancerSkill.query.filter_by(freelancer_user_id=freelancer_user_id, skill_id=skill_id).first()
        if existing_fs:
            raise InvalidUsageException("您已添加过该技能。", error_code=40901)

        freelancer_skill = FreelancerSkill(
            freelancer_user_id=freelancer_user_id,
            skill_id=skill_id,
            proficiency_level=data.get('proficiency_level'),
            years_of_experience=data.get('years_of_experience'),
            certificate_url=data.get('certificate_url')
            # certificate_verified defaults to False in model
        )
        db.session.add(freelancer_skill)
        try:
            db.session.commit()
            return freelancer_skill
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"为零工添加技能失败: {str(e)}", status_code=500, error_code=50001)

    def update_freelancer_skill(self, freelancer_user_id, skill_id, data):
        user = User.query.get(freelancer_user_id)
        if not user or 'freelancer' not in user.available_roles:
            raise AuthorizationException("仅零工用户可以更新技能。", error_code=40302)

        freelancer_skill = FreelancerSkill.query.filter_by(freelancer_user_id=freelancer_user_id, skill_id=skill_id).first()
        if not freelancer_skill:
            raise NotFoundException("零工未关联此技能，无法更新。")

        # Fields that can be updated
        if 'proficiency_level' in data:
            freelancer_skill.proficiency_level = data['proficiency_level']
        if 'years_of_experience' in data:
            freelancer_skill.years_of_experience = data['years_of_experience']
        if 'certificate_url' in data:
            freelancer_skill.certificate_url = data['certificate_url']
            # If URL changes, verification status should probably reset or be re-evaluated by admin
            # freelancer_skill.certificate_verified = False 

        try:
            db.session.commit()
            return freelancer_skill
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"更新零工技能失败: {str(e)}", status_code=500, error_code=50001)

    def remove_skill_from_freelancer(self, freelancer_user_id, skill_id):
        user = User.query.get(freelancer_user_id)
        if not user or 'freelancer' not in user.available_roles:
            raise AuthorizationException("仅零工用户可以移除技能。", error_code=40302)

        freelancer_skill = FreelancerSkill.query.filter_by(freelancer_user_id=freelancer_user_id, skill_id=skill_id).first()
        if not freelancer_skill:
            raise NotFoundException("零工未关联此技能，无法移除。")

        db.session.delete(freelancer_skill)
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"移除零工技能失败: {str(e)}", status_code=500, error_code=50001)

skill_service = SkillService()