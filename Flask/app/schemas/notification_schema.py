"""Notification Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from ..models.notification import NotificationTypeEnum

class NotificationSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True) # Notifications are usually targeted
    notification_type = fields.String(required=True, validate=validate.OneOf([e.value for e in NotificationTypeEnum]))
    title = fields.String(required=True, validate=validate.Length(max=100))
    content = fields.String(required=True, validate=validate.Length(max=1000))
    related_resource_type = fields.String(validate=validate.Length(max=50))
    related_resource_id = fields.Integer()
    is_read = fields.Boolean(dump_only=True, dump_default=False)
    read_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # Add a field for potential actions or links
    # e.g., link = fields.URL(dump_only=True)

    class Meta:
        ordered = True

class NotificationMarkReadSchema(ma.Schema):
    # Similar to messages, could mark specific IDs or all up to a point/time
    notification_ids = fields.List(fields.Integer(), required=False, validate=validate.Length(min=1))
    mark_all_as_read = fields.Boolean(required=False) # Option to mark all

    @validates_schema
    def check_conditions(self, data, **kwargs):
        if not data.get('notification_ids') and not data.get('mark_all_as_read'):
            raise ValidationError("Either 'notification_ids' or 'mark_all_as_read=True' must be provided.")
        if data.get('notification_ids') and data.get('mark_all_as_read'):
            raise ValidationError("Provide either 'notification_ids' or 'mark_all_as_read=True', not both.")

# Schema for creating notifications (usually internal/admin task)
class NotificationCreateSchema(ma.Schema):
    user_id = fields.Integer(required=True) # Target user
    notification_type = fields.String(required=True, validate=validate.OneOf([e.value for e in NotificationTypeEnum]))
    title = fields.String(required=True, validate=validate.Length(max=100))
    content = fields.String(required=True, validate=validate.Length(max=1000))
    related_resource_type = fields.String(validate=validate.Length(max=50))
    related_resource_id = fields.Integer()
