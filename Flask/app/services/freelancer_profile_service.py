from ..models.user import User
from ..models.profile import FreelancerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException
from datetime import date

class FreelancerProfileService:
    def get_profile_by_user_id(self, user_id):
        """
        获取用户的零工档案
        :param user_id: 用户ID或UUID
        :return: FreelancerProfile对象
        :raises: NotFoundException
        """
        # 尝试以不同方式查找用户
        user = None
        try:
            # 首先尝试作为整数ID查找
            if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
                user = User.query.get(int(user_id))
            # 然后尝试作为UUID查找
            elif isinstance(user_id, str):
                user = User.query.filter_by(uuid=user_id).first()
        except Exception as e:
            # 记录异常但继续尝试正常流程
            from flask import current_app
            current_app.logger.warning(f"查找用户时出现异常: {str(e)}")
        
        # 如果找到了用户，查找其档案
        if user:
            profile = FreelancerProfile.query.filter_by(user_id=user.id).first()
            if profile:
                return profile
            else:
                # 用户存在但没有档案
                raise NotFoundException(message="未找到零工档案。您可以先创建一个。", error_code=40401)
        
        # 用户不存在
        raise NotFoundException(message="用户不存在。", error_code=40401)

    def create_or_update_profile(self, user_id, data, is_creation=False):
        """
        创建或更新零工档案
        :param user_id: 用户ID或UUID
        :param data: 档案数据
        :param is_creation: 是否是创建操作
        :return: FreelancerProfile对象
        :raises: NotFoundException, AuthorizationException, InvalidUsageException, BusinessException
        """
        # 尝试以不同方式查找用户
        user = None
        try:
            # 首先尝试作为整数ID查找
            if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
                user = User.query.get(int(user_id))
            # 然后尝试作为UUID查找
            elif isinstance(user_id, str):
                user = User.query.filter_by(uuid=user_id).first()
        except Exception as e:
            # 记录异常
            from flask import current_app
            current_app.logger.error(f"查找用户时出现异常: {str(e)}")
        
        if not user:
            raise NotFoundException(message="用户不存在。", error_code=40401)

        from flask import current_app
        current_app.logger.info(f"用户角色: {user.available_roles}, 当前角色: {user.current_role}")

        # 检查用户是否有零工角色
        has_freelancer_role = False
        if hasattr(user, 'available_roles'):
            if isinstance(user.available_roles, list) and 'freelancer' in user.available_roles:
                has_freelancer_role = True
            elif isinstance(user.available_roles, str) and 'freelancer' in user.available_roles:
                has_freelancer_role = True
        
        if not has_freelancer_role and user.current_role != 'freelancer':
            raise AuthorizationException(message="用户不是零工角色，无法操作零工档案。", error_code=40302)

        profile = FreelancerProfile.query.filter_by(user_id=user.id).first()

        if is_creation and profile:
            raise InvalidUsageException(message="零工档案已存在，请使用更新接口。", error_code=40901) # Conflict
        
        if not profile:
            if not is_creation:
                 # If trying to update a non-existent profile, and not explicitly creating
                 # we could either create it, or raise an error. Let's require explicit creation or existence.
                 raise NotFoundException(message="零工档案不存在，无法更新。请先创建。", error_code=40401)
            profile = FreelancerProfile(user_id=user.id)
            db.session.add(profile)
        
        # Fields from freelancer_profiles table (createDB.sql)
        allowed_fields = [
            'real_name', 
            # 'id_card_number_encrypted', # Removed, should be handled by verification process
            'gender', 'birth_date',
            'avatar_url', 'nickname', 'location_province', 'location_city',
            'location_district', 'bio', 'work_preference' # work_preference is JSON
            # 'verification_status' and 'credit_score' are usually system-managed or via specific processes
        ]

        for field in allowed_fields:
            if field in data:
                value = data[field]
                if field == 'birth_date' and isinstance(value, str):
                    try:
                        # 确保日期格式正确处理，包括所有可能的ISO 8601格式
                        value = value.replace('Z', '+00:00')
                        value = date.fromisoformat(value)
                    except ValueError as e:
                        current_app.logger.error(f"日期格式转换失败: {str(e)}, 值: {value}")
                        raise InvalidUsageException(message=f"字段 '{field}' 日期格式无效，请使用 YYYY-MM-DD。")
                # For JSON fields like work_preference, ensure data is appropriate (dict/list)
                # SQLAlchemy handles JSON type conversion if data[field] is a Python dict/list
                setattr(profile, field, value)

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            # Log error e
            from flask import current_app
            current_app.logger.error(f"保存零工档案失败: {str(e)}")
            action = "创建" if is_creation or not profile.id else "更新"
            raise BusinessException(message=f"{action}零工档案失败: {str(e)}", status_code=500, error_code=50001)

    # Convenience method specifically for creation
    def create_profile(self, user_id, data):
        return self.create_or_update_profile(user_id, data, is_creation=True)

    # Convenience method specifically for update
    def update_profile(self, user_id, data):
        return self.create_or_update_profile(user_id, data, is_creation=False)

freelancer_profile_service = FreelancerProfileService() 