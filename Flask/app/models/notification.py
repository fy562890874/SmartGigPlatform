"""Notification Model"""
from ..core.extensions import db
from datetime import datetime
import enum

# --- Enums for Notification ---
class NotificationTypeEnum(enum.Enum):
    system_announcement = 'system_announcement'
    job_recommendation = 'job_recommendation'
    application_update = 'application_update'
    order_update = 'order_update'
    payment_update = 'payment_update'
    evaluation_reminder = 'evaluation_reminder'
    policy_update = 'policy_update'
    verification_result = 'verification_result'
    report_result = 'report_result'
    dispute_update = 'dispute_update'

# --- Notification Model ---
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='通知ID')
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='接收用户ID')
    notification_type = db.Column(db.Enum(NotificationTypeEnum), nullable=False, index=True, comment='通知类型')
    title = db.Column(db.String(100), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    related_resource_type = db.Column(db.String(50), nullable=True, comment='关联业务资源类型')
    related_resource_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=True, comment='关联业务资源ID')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True, comment='是否已读')
    read_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='阅读时间')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # --- Relationships ---
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id} (User: {self.user_id}, Type: {self.notification_type.name})>'
