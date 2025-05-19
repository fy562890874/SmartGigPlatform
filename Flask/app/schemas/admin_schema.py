"""Admin Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate
from ..models.admin import AdminStatusEnum

class AdminUserSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    password = fields.String(load_only=True, required=True, validate=validate.Length(min=6))
    real_name = fields.String(validate=validate.Length(max=50))
    role = fields.String(required=True, validate=validate.Length(max=50)) # Consider using Enum validation if roles are fixed
    status = fields.String(validate=validate.OneOf([e.value for e in AdminStatusEnum]), dump_default=AdminStatusEnum.active.value)
    last_login_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        ordered = True

class AdminUserUpdateSchema(ma.Schema):
    real_name = fields.String(validate=validate.Length(max=50))
    role = fields.String(validate=validate.Length(max=50))
    status = fields.String(validate=validate.OneOf([e.value for e in AdminStatusEnum]))
    # Password update might need a separate schema/endpoint

class AdminUserLoginSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True, load_only=True)
