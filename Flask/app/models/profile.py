"""Profile Models (Freelancer & Employer)"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON

# --- Enums for Profiles ---
class GenderEnum(enum.Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    unknown = 'unknown'

class VerificationStatusEnum(enum.Enum):
    unverified = 'unverified'
    pending = 'pending_review'
    verified = 'verified'
    rejected = 'rejected'

class EmployerProfileTypeEnum(enum.Enum):
    individual = 'individual'
    company = 'company'

# --- Freelancer Profile Model ---
class FreelancerProfile(db.Model):
    __tablename__ = 'freelancer_profiles'

    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id'), primary_key=True, comment='关联用户ID')
    
    real_name = db.Column(db.String(100), nullable=True, comment='真实姓名')
    # id_card_number_encrypted = db.Column(db.String(255), nullable=True, comment='身份证号 (加密存储)') 
    
    gender = db.Column(db.Enum(GenderEnum), nullable=True, default=GenderEnum.unknown, comment='性别')
    birth_date = db.Column(db.Date, nullable=True, comment='出生日期')
    
    avatar_url = db.Column(db.String(512), nullable=True, comment='头像URL')
    nickname = db.Column(db.String(100), nullable=True, comment='昵称')
    
    location_province = db.Column(db.String(50), nullable=True, comment='常驻省份')
    location_city = db.Column(db.String(50), nullable=True, comment='常驻城市')
    location_district = db.Column(db.String(50), nullable=True, comment='常驻区县')
    
    bio = db.Column(db.Text, nullable=True, comment='个人简介')
    work_preference = db.Column(JSON, nullable=True, comment='工作偏好 (JSON对象)')
    
    verification_status = db.Column(db.Enum(VerificationStatusEnum), nullable=False, default=VerificationStatusEnum.unverified, comment='实名认证状态')
    verification_record_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('verification_records.id'), nullable=True, comment='关联的验证记录ID')

    credit_score = db.Column(db.Integer, nullable=False, default=100, comment='信用分')
    average_rating = db.Column(db.Numeric(3, 2), nullable=True, comment='平均评分')
    total_orders_completed = db.Column(db.Integer, nullable=False, default=0, comment='累计完成订单数')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='freelancer_profile')
    verification_record = db.relationship('VerificationRecord', back_populates='freelancer_profile_verified', foreign_keys=[verification_record_id])

    def __repr__(self):
        return f'<FreelancerProfile user_id={self.user_id} nickname={self.nickname}>'


# --- Employer Profile Model ---
class EmployerProfile(db.Model):
    __tablename__ = 'employer_profiles'

    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id'), primary_key=True, comment='关联用户ID')
    
    profile_type = db.Column(db.Enum(EmployerProfileTypeEnum), nullable=False, comment='档案类型 (企业/个人雇主)')
    
    # Common fields for both individual and company employer
    real_name = db.Column(db.String(100), nullable=True, comment='联系人真实姓名/个体经营者姓名')
    avatar_url = db.Column(db.String(512), nullable=True, comment='头像URL (个人)或公司Logo URL')
    nickname = db.Column(db.String(100), nullable=True, comment='雇主昵称/公司简称')
    
    location_province = db.Column(db.String(50), nullable=True, comment='所在地省份')
    location_city = db.Column(db.String(50), nullable=True, comment='所在地城市')
    location_district = db.Column(db.String(50), nullable=True, comment='所在地区县')
    contact_phone = db.Column(db.String(30), nullable=True, comment='公开联系电话') # Increased length for international

    verification_status = db.Column(db.Enum(VerificationStatusEnum), nullable=False, default=VerificationStatusEnum.unverified, comment='认证状态')
    verification_record_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('verification_records.id'), nullable=True, comment='关联的验证记录ID')

    credit_score = db.Column(db.Integer, nullable=False, default=100, comment='信用分')
    average_rating = db.Column(db.Numeric(3, 2), nullable=True, comment='收到的平均评分')
    total_jobs_posted = db.Column(db.Integer, nullable=False, default=0, comment='累计发布工作数')

    # Company-specific fields (nullable if profile_type is 'individual')
    company_name = db.Column(db.String(200), nullable=True, comment='公司全称')
    # business_license_number: Store encrypted or handle via VerificationRecord. For now, assume it's part of verification data.
    # business_license_number_encrypted = db.Column(db.String(255), nullable=True, comment='营业执照号 (加密存储)')
    # business_license_photo_url: Store path to file. Handled by VerificationRecord.
    # business_license_photo_url = db.Column(db.String(512), nullable=True, comment='营业执照照片URL')
    company_address = db.Column(db.String(255), nullable=True, comment='公司详细地址')
    company_description = db.Column(db.Text, nullable=True, comment='公司简介')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    user = db.relationship('User', back_populates='employer_profile')
    verification_record = db.relationship('VerificationRecord', back_populates='employer_profile_verified', foreign_keys=[verification_record_id])

    def __repr__(self):
        return f'<EmployerProfile user_id={self.user_id} name={self.company_name or self.real_name}>'
