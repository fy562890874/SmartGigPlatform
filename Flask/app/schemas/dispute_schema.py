"""Dispute Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate
from ..models.dispute import DisputeStatusEnum

# Nested Schemas (simplified for now)
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)

class OrderBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)

class AdminUserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(dump_only=True)


class DisputeSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    order_id = fields.Integer(required=True, load_only=True) # Load only for creation
    initiator_user_id = fields.Integer(dump_only=True) # Set internally based on JWT
    reason = fields.String(required=True, validate=validate.Length(min=10))
    expected_resolution = fields.String()
    attachments = fields.List(fields.URL(), description="List of evidence attachment URLs") # Assuming URLs are stored
    status = fields.String(validate=validate.OneOf([e.value for e in DisputeStatusEnum]), dump_default=DisputeStatusEnum.pending.value)
    resolution_result = fields.String(dump_only=True)
    platform_mediator_id = fields.Integer(dump_only=True)
    resolved_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    order = fields.Nested(OrderBasicSchema, dump_only=True)
    initiator = fields.Nested(UserBasicSchema, dump_only=True, attribute="initiator_user")
    platform_mediator = fields.Nested(AdminUserBasicSchema, dump_only=True)

    class Meta:
        ordered = True

class DisputeCreateSchema(ma.Schema):
    order_id = fields.Integer(required=True)
    reason = fields.String(required=True, validate=validate.Length(min=10, max=1000))
    expected_resolution = fields.String(validate=validate.Length(max=1000))
    attachments = fields.List(fields.URL(), description="List of evidence attachment URLs")

class DisputeUpdateSchema(ma.Schema): # For platform mediator
    status = fields.String(required=True, validate=validate.OneOf([e.value for e in DisputeStatusEnum]))
    resolution_result = fields.String(validate=validate.Length(max=1000))
