"""Message Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate
from ..models.message import MessageTypeEnum

# Basic Schemas for Nesting
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)
    avatar_url = fields.URL(dump_only=True)

class MessageSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    conversation_id = fields.String(dump_only=True) # Usually generated/retrieved by service
    sender_id = fields.Integer(dump_only=True) # Set from JWT or system
    recipient_id = fields.Integer(required=True) # Required for sending
    content = fields.String(required=True, validate=validate.Length(min=1, max=2000))
    message_type = fields.String(
        validate=validate.OneOf([e.value for e in MessageTypeEnum]),
        dump_default=MessageTypeEnum.text.value,
        load_default=MessageTypeEnum.text.value # Default to text if not provided on input
    )
    related_resource_type = fields.String(validate=validate.Length(max=50))
    related_resource_id = fields.Integer()
    is_read = fields.Boolean(dump_only=True, dump_default=False)
    read_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    sender = fields.Nested(UserBasicSchema, dump_only=True)
    recipient = fields.Nested(UserBasicSchema, dump_only=True)

    class Meta:
        ordered = True

class MessageCreateSchema(ma.Schema):
    recipient_id = fields.Integer(required=True)
    content = fields.String(required=True, validate=validate.Length(min=1, max=2000))
    # message_type: Optional, defaults to 'text'
    message_type = fields.String(validate=validate.OneOf([e.value for e in MessageTypeEnum]))
    # related_resource: Optional, could be validated based on type
    related_resource_type = fields.String(validate=validate.Length(max=50))
    related_resource_id = fields.Integer()
    # conversation_id might be passed if continuing a conversation, or determined by service
    conversation_id = fields.String(validate=validate.Length(max=64))

class MessageMarkReadSchema(ma.Schema):
    # Typically, the request might be a PUT to /conversations/{conv_id}/read
    # or POST /messages/mark_read with a list of message IDs or conversation ID.
    # If marking specific messages:
    message_ids = fields.List(fields.Integer(), required=True, validate=validate.Length(min=1))
    # If marking a conversation up to a certain point:
    # conversation_id = fields.String(required=True)
    # last_read_message_id = fields.Integer(required=True) # Or timestamp
