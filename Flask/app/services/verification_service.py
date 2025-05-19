from ..models.user import User
from ..models.verification import VerificationRecord
from ..models.profile import FreelancerProfile
from ..models.profile import EmployerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException
from datetime import datetime

class VerificationService:
    def submit_verification(self, user_id, data):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundException("用户不存在。")

        profile_type = data.get('profile_type')
        submitted_data = data.get('submitted_data') # This should be validated by a schema

        if not profile_type or not submitted_data:
            raise InvalidUsageException("认证类型和认证数据不能为空。")

        # Basic validation based on profile_type
        if profile_type == 'freelancer':
            profile = FreelancerProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                raise NotFoundException("提交认证前，请先创建零工档案。")
        elif profile_type in ['employer_individual', 'employer_company']:
            profile = EmployerProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                raise NotFoundException("提交认证前，请先创建雇主档案。")
            if profile_type == 'employer_company' and not profile.company_name:
                 raise InvalidUsageException("企业认证前，请在雇主档案中填写公司名称。")
        else:
            raise InvalidUsageException("无效的档案类型。")

        # 使用枚举值处理状态
        from ..models.verification import VerificationRecordStatusEnum

        # Check for existing pending or approved verification for this profile type
        existing_pending_or_approved = VerificationRecord.query.filter_by(user_id=user_id, profile_type=profile_type)\
                                                   .filter(VerificationRecord.status.in_([
                                                        VerificationRecordStatusEnum.pending.value, 
                                                        VerificationRecordStatusEnum.approved.value
                                                    ]))\
                                                   .first()
        if existing_pending_or_approved:
            existing_status = existing_pending_or_approved.status
            if hasattr(existing_pending_or_approved.status, 'value'):
                existing_status = existing_pending_or_approved.status.value
            raise InvalidUsageException(f"您已提交过 {profile_type} 类型的认证申请，当前状态为: {existing_status}。", error_code=40901)

        # 使用枚举对象创建记录
        verification_record = VerificationRecord(
            user_id=user_id,
            profile_type=profile_type,
            submitted_data=submitted_data, # Schema should ensure this is a valid JSON/dict
            status=VerificationRecordStatusEnum.pending
        )
        db.session.add(verification_record)
        try:
            db.session.commit()
            # Update profile status to 'pending' if it was 'unverified' or 'failed'
            if profile and profile.verification_status in ['unverified', 'failed']:
                profile.verification_status = 'pending'
                profile.verification_record_id = verification_record.id # Link to the new record
                db.session.commit()
            return verification_record
        except Exception as e:
            db.session.rollback()
            # Log error e
            raise BusinessException(message=f"提交认证申请失败: {str(e)}", status_code=500, error_code=50001)

    def get_user_verification_records(self, user_id, profile_type=None, page=1, per_page=10):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundException("用户不存在。")

        query = VerificationRecord.query.filter_by(user_id=user_id)
        if profile_type:
            query = query.filter_by(profile_type=profile_type)
        
        query = query.order_by(VerificationRecord.created_at.desc())
        paginated_records = query.paginate(page=page, per_page=per_page, error_out=False)
        return paginated_records

verification_service = VerificationService() 