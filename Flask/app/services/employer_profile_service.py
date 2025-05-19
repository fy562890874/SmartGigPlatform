from ..models.user import User
from ..models.profile import EmployerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException

class EmployerProfileService:
    def get_profile_by_user_id(self, user_id):
        profile = EmployerProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            user = User.query.get(user_id)
            if not user:
                raise NotFoundException(message="用户不存在。")
            raise NotFoundException(message="未找到雇主档案。您可以先创建一个。", error_code=40401)
        return profile

    def create_or_update_profile(self, user_id, data, is_creation=False):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundException(message="用户不存在。")

        if 'employer' not in user.available_roles and user.current_role != 'employer':
            raise AuthorizationException(message="用户不是雇主角色，无法操作雇主档案。", error_code=40302)

        profile = EmployerProfile.query.filter_by(user_id=user_id).first()

        if is_creation and profile:
            raise InvalidUsageException(message="雇主档案已存在，请使用更新接口。", error_code=40901)
        
        if not profile:
            if not is_creation:
                 raise NotFoundException(message="雇主档案不存在，无法更新。请先创建。", error_code=40401)
            profile = EmployerProfile(user_id=user_id)
            db.session.add(profile)
        
        # Fields from employer_profiles table (createDB.sql)
        allowed_fields = [
            'profile_type', 'real_name', 'id_card_number_encrypted', 'avatar_url',
            'nickname', 'location_province', 'location_city', 'location_district',
            'contact_phone', 'company_name', 'business_license_number',
            'business_license_photo_url', 'company_address', 'company_description'
            # 'verification_status' and 'credit_score' are usually system-managed
        ]

        for field in allowed_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        # Ensure profile_type is valid if provided
        if 'profile_type' in data and data['profile_type'] not in ['individual', 'company']:
            raise InvalidUsageException(message="无效的档案类型，必须是 'individual' 或 'company'。")

        try:
            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            action = "创建" if is_creation or not profile.id else "更新"
            raise BusinessException(message=f"{action}雇主档案失败: {str(e)}", status_code=500, error_code=50001)

    def create_profile(self, user_id, data):
        return self.create_or_update_profile(user_id, data, is_creation=True)

    def update_profile(self, user_id, data):
        return self.create_or_update_profile(user_id, data, is_creation=False)

employer_profile_service = EmployerProfileService() 