"""Report Model"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON

# --- Enums for Report ---
class ReportTypeEnum(enum.Enum):
    job = 'job'
    user = 'user'
    order = 'order'
    message = 'message'
    evaluation = 'evaluation'

class ReportStatusEnum(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    resolved_valid = 'resolved_valid'
    resolved_invalid = 'resolved_invalid'
    resolved_duplicate = 'resolved_duplicate'

# --- Report Model ---
class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True)
    reporter_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='举报者用户ID')
    report_type = db.Column(db.Enum(ReportTypeEnum), nullable=False, index=True, comment='举报对象类型')
    target_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=False, index=True, comment='被举报对象的ID')
    reason_category = db.Column(db.String(50), nullable=False, comment='举报原因分类')
    reason_description = db.Column(db.Text, nullable=True, comment='举报原因详述')
    attachments = db.Column(JSON, nullable=True, comment='附件URL列表 (JSON 数组)')
    status = db.Column(db.Enum(ReportStatusEnum), nullable=False, default=ReportStatusEnum.pending, index=True, comment='处理状态')
    processor_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('admin_users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='处理管理员ID')
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='处理时间')
    processing_result = db.Column(db.Text, nullable=True, comment='处理结果描述/操作记录')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    reporter = db.relationship('User', back_populates='reports_made', foreign_keys=[reporter_user_id])
    processor = db.relationship('AdminUser', back_populates='processed_reports')
    # Polymorphic relationship for target is complex. Handled in service layer.

    def __repr__(self):
        return f'<Report {self.id} (Reporter: {self.reporter_user_id}, Type: {self.report_type.name}, Target: {self.target_id})>'
