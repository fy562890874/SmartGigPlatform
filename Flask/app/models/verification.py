"""Verification Record Model"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON

# --- Enums for VerificationRecord ---
class VerificationProfileTypeEnum(enum.Enum):
    freelancer = 'freelancer'
    employer_individual = 'employer_individual'
    employer_company = 'employer_company'

class VerificationRecordStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

# --- VerificationRecord Model ---
class VerificationRecord(db.Model):
    __tablename__ = 'verification_records'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='认证记录ID')
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='申请用户ID')
    profile_type = db.Column(db.Enum(VerificationProfileTypeEnum), nullable=False, index=True, comment='申请认证的档案类型')
    submitted_data = db.Column(JSON, nullable=False, comment='提交的认证资料 (JSON)')
    status = db.Column(db.Enum(VerificationRecordStatusEnum), nullable=False, default=VerificationRecordStatusEnum.pending, index=True, comment='审核状态')
    reviewer_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('admin_users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='审核管理员ID')
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='审核时间')
    rejection_reason = db.Column(db.Text, nullable=True, comment='拒绝原因')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    user = db.relationship('User', back_populates='verification_records')
    reviewer = db.relationship('AdminUser', back_populates='reviewed_verifications')
    # Relationships back from profiles are defined in profile.py
    freelancer_profile_verified = db.relationship('FreelancerProfile', back_populates='verification_record', uselist=False, foreign_keys='FreelancerProfile.verification_record_id')
    employer_profile_verified = db.relationship('EmployerProfile', back_populates='verification_record', uselist=False, foreign_keys='EmployerProfile.verification_record_id')

    def __repr__(self):
        return f'<VerificationRecord {self.id} (User: {self.user_id}, Type: {self.profile_type.name}, Status: {self.status.name})>'
