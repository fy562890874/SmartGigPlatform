"""Favorite Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, ValidationError, validates
from ..models.favorite import FavoriteTypeEnum

# Basic Schemas for nested representation
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)
    avatar_url = fields.URL(dump_only=True)

class JobBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)
    # Add other relevant fields like status, salary etc. if needed for list view

class FavoriteSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True) # Set from JWT
    favorite_type = fields.String(required=True, validate=validate.OneOf([e.value for e in FavoriteTypeEnum]))
    target_id = fields.Integer(required=True)
    created_at = fields.DateTime(dump_only=True)

    # Dynamically nested target based on favorite_type (for output)
    target = fields.Method("get_target_object", dump_only=True)

    def get_target_object(self, obj):
        if obj.favorite_type == FavoriteTypeEnum.job:
            # Assuming obj.job relationship exists and is loaded
            return JobBasicSchema().dump(obj.job) if obj.job else None
        elif obj.favorite_type in [FavoriteTypeEnum.freelancer, FavoriteTypeEnum.employer]:
             # Assuming obj.target_user relationship exists and is loaded
            return UserBasicSchema().dump(obj.target_user) if obj.target_user else None
        return None

    class Meta:
        ordered = True
        # Exclude target_id from output if target is present
        # exclude = ("target_id",)


class FavoriteCreateSchema(ma.Schema):
    favorite_type = fields.String(required=True, validate=validate.OneOf([e.value for e in FavoriteTypeEnum]))
    target_id = fields.Integer(required=True)

    @validates('target_id')
    def validate_target_id(self, value):
        if value <= 0:
            raise ValidationError("target_id must be a positive integer.")

class FavoriteListSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    favorite_type = fields.String(dump_only=True)
    target_id = fields.Integer(dump_only=True) # Keep target_id for potential client-side linking
    created_at = fields.DateTime(dump_only=True)

    # Include nested object details in list view
    target = fields.Method("get_target_object", dump_only=True)

    def get_target_object(self, obj):
        if obj.favorite_type == FavoriteTypeEnum.job:
            return JobBasicSchema().dump(obj.job) if hasattr(obj, 'job') and obj.job else None
        elif obj.favorite_type in [FavoriteTypeEnum.freelancer, FavoriteTypeEnum.employer]:
            return UserBasicSchema().dump(obj.target_user) if hasattr(obj, 'target_user') and obj.target_user else None
        return None

    class Meta:
        ordered = True
