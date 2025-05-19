"""User Schemas for Serialization/Deserialization"""
from ..core.extensions import ma # Marshmallow instance from extensions
from marshmallow import fields, validate, validates, ValidationError

# Basic User Schema for output (read-only fields included)
class UserSchema(ma.Schema):
    id = fields.Integer(dump_only=True) # Added id
    uuid = fields.UUID(dump_only=True) # Use UUID field type
    phone_number = fields.String(dump_only=True) # Usually not editable directly, maybe separate endpoint
    email = fields.String(dump_only=True, allow_none=True) # Added email
    nickname = fields.String(allow_none=True) # Allow nickname to be null if not set
    avatar_url = fields.URL(allow_none=True) # Allow avatar to be null
    # user_type = fields.String(dump_only=True) # Replaced by current_role and available_roles
    current_role = fields.String(dump_only=True) # Added
    available_roles = fields.List(fields.String(), dump_only=True) # Added
    status = fields.String(dump_only=True) # Managed internally
    last_login_at = fields.DateTime(dump_only=True, allow_none=True) # Added
    registered_at = fields.DateTime(dump_only=True) # Added
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        # Define fields to include/exclude if needed
        # fields = ('uuid', 'nickname', 'avatar_url', 'user_type')
        ordered = True

# 公开用户信息模式，用于其他用户或公开场景展示
class UserPublicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)
    avatar_url = fields.URL(dump_only=True, allow_none=True)
    current_role = fields.String(dump_only=True)

    class Meta:
        ordered = True

# Schema for User Registration Input
class UserRegistrationSchema(ma.Schema):
    phone_number = fields.String(required=True, validate=validate.Length(min=5, max=20)) # Add specific validation
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6)) # load_only hides from output
    user_type = fields.String(required=False, validate=validate.OneOf(['freelancer', 'employer']), missing='freelancer') # Changed enum, made optional with default for service
    nickname = fields.String(validate=validate.Length(max=50), allow_none=True) # Allow none for registration

    # Example custom validation
    @validates('phone_number')
    def validate_phone(self, value):
        # Add more complex phone number validation if needed
        if not value.isdigit():
            # This is a basic example, real validation might be more complex
            # raise ValidationError("Phone number must contain only digits.")
            pass # Allow non-digits for now, adjust as needed

# Schema for User Login Input
class UserLoginSchema(ma.Schema):
    phone_number = fields.String(required=True)
    password = fields.String(required=True, load_only=True)

# Schema for User Profile Update Input
class UserProfileUpdateSchema(ma.Schema):
    nickname = fields.String(validate=validate.Length(max=50))
    avatar_url = fields.URL() # Validate if it's a URL

    # Ensure at least one field is provided for update
    @validates
    def validate_non_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field (nickname or avatar_url) must be provided for update.")

