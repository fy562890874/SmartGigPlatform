"""Dispute Model"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON

# --- Enums for Dispute ---
class DisputeStatusEnum(enum.Enum):
    pending = 'pending'
    negotiating = 'negotiating'
    platform_intervening = 'platform_intervening'
    resolved = 'resolved'
    closed = 'closed'

# --- Dispute Model ---
class Dispute(db.Model):
    __tablename__ = 'disputes'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False, index=True, comment='关联的订单ID')
    initiator_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='发起争议的用户ID')
    reason = db.Column(db.Text, nullable=False, comment='争议原因描述')
    expected_resolution = db.Column(db.Text, nullable=True, comment='发起者期望的解决方案')
    attachments = db.Column(JSON, nullable=True, comment='相关证据附件URL列表 (JSON 数组)')
    status = db.Column(db.Enum(DisputeStatusEnum), nullable=False, default=DisputeStatusEnum.pending, index=True, comment='争议状态')
    resolution_result = db.Column(db.Text, nullable=True, comment='最终解决方案/处理结果')
    platform_mediator_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('admin_users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='平台介入处理人ID')
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='解决时间')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    order = db.relationship('Order', back_populates='dispute')
    initiator = db.relationship('User', back_populates='disputes_initiated', foreign_keys=[initiator_user_id])
    platform_mediator = db.relationship('AdminUser', back_populates='mediated_disputes')

    def __repr__(self):
        return f'<Dispute {self.id} (Order: {self.order_id}, Status: {self.status.name})>'
