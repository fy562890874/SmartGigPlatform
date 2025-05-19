"""Message Model"""
from ..core.extensions import db
from datetime import datetime
import enum

# --- Enums for Message ---
class MessageTypeEnum(enum.Enum):
    text = 'text'
    image = 'image'
    audio = 'audio'
    file = 'file'
    system_notification = 'system_notification' # For instant system messages, different from structured Notifications
    order_update = 'order_update'
    application_update = 'application_update'

# --- Message Model ---
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='消息唯一ID')
    conversation_id = db.Column(db.String(64), nullable=False, index=True, comment='会话ID')
    sender_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='发送者用户ID (系统消息时为空)')
    recipient_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='接收者用户ID')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    message_type = db.Column(db.Enum(MessageTypeEnum), nullable=False, default=MessageTypeEnum.text, comment='消息类型')
    related_resource_type = db.Column(db.String(50), nullable=True, comment='关联业务资源类型')
    related_resource_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=True, comment='关联业务资源ID')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True, comment='接收方是否已读')
    read_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='接收方阅读时间')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    # updated_at is usually not needed for messages

    # --- Relationships ---
    sender = db.relationship('User', back_populates='messages_sent', foreign_keys=[sender_id])
    recipient = db.relationship('User', back_populates='messages_received', foreign_keys=[recipient_id])

    def __repr__(self):
        return f'<Message {self.id} (From: {self.sender_id} To: {self.recipient_id})>'
