"""System Config Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate

class SystemConfigSchema(ma.Schema):
    config_key = fields.String(required=True, validate=validate.Length(min=1, max=100))
    config_value = fields.String(required=True) # Value can be complex, validation depends on key
    description = fields.String(validate=validate.Length(max=255))
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        ordered = True

class SystemConfigUpdateSchema(ma.Schema):
    config_value = fields.String(required=True)
    # Description might also be updatable
    description = fields.String(validate=validate.Length(max=255))

# No Create Schema usually, configs are often pre-defined or managed differently.
# If creation is allowed:
# class SystemConfigCreateSchema(SystemConfigSchema):
#     class Meta:
#         exclude = ("updated_at",)
