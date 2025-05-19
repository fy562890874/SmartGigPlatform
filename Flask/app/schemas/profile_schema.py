""""Profile Schemas (Freelancer & Employer)"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from ..models.profile import GenderEnum, VerificationStatusEnum, EmployerProfileTypeEnum
# Assuming UserSchema exists for the base user info
from .user_schema import UserSchema

# --- Freelancer Profile Schema ---
class FreelancerProfileSchema(ma.Schema):
    user_id = fields.Integer(dump_only=True)
    real_name = fields.String(validate=validate.Length(max=50))
    # id_card_number_encrypted: Should not be exposed via API
    gender = fields.String(validate=validate.OneOf([e.value for e in GenderEnum]), dump_default=GenderEnum.unknown.value)
    birth_date = fields.Date()
    avatar_url = fields.URL(validate=validate.Length(max=512))
    nickname = fields.String(validate=validate.Length(max=50))
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    bio = fields.String(validate=validate.Length(max=1000))
    work_preference = fields.Dict() # JSON field, structure depends on definition
    verification_status = fields.String(validate=validate.OneOf([e.value for e in VerificationStatusEnum]), dump_only=True, dump_default=VerificationStatusEnum.unverified.value)
    verification_record_id = fields.Integer(dump_only=True) # Internal link

    credit_score = fields.Integer(dump_only=True, dump_default=100)
    average_rating = fields.Decimal(places=2, as_string=True, dump_only=True)
    total_orders_completed = fields.Integer(dump_only=True, dump_default=0)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Nest basic user info?
    # user = fields.Nested(UserSchema(only=("uuid", "phone_number", "status")), dump_only=True)

    class Meta:
        ordered = True

class FreelancerProfileUpdateSchema(ma.Schema):
    # Allow updating specific fields
    # real_name, id_card_number are usually part of verification, not direct update
    gender = fields.String(validate=validate.OneOf([e.value for e in GenderEnum]))
    birth_date = fields.Date()
    avatar_url = fields.URL(validate=validate.Length(max=512))
    nickname = fields.String(validate=validate.Length(max=50))
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    bio = fields.String(validate=validate.Length(max=1000))
    work_preference = fields.Dict()

    @validates_schema
    def check_at_least_one_field(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided for update.")


# --- Employer Profile Schema ---
class EmployerProfileSchema(ma.Schema):
    user_id = fields.Integer(dump_only=True)
    profile_type = fields.String(validate=validate.OneOf([e.value for e in EmployerProfileTypeEnum]), required=True) # Required on creation/view
    real_name = fields.String(validate=validate.Length(max=50)) # Contact person for company
    # id_card_number_encrypted: Should not be exposed (maybe for individual type verification)
    avatar_url = fields.URL(validate=validate.Length(max=512)) # Logo for company
    nickname = fields.String(validate=validate.Length(max=50)) # Short name for company
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    contact_phone = fields.String(validate=validate.Length(max=20)) # Public contact?
    verification_status = fields.String(validate=validate.OneOf([e.value for e in VerificationStatusEnum]), dump_only=True, dump_default=VerificationStatusEnum.unverified.value)
    verification_record_id = fields.Integer(dump_only=True)

    credit_score = fields.Integer(dump_only=True, dump_default=100)
    average_rating = fields.Decimal(places=2, as_string=True, dump_only=True)
    total_jobs_posted = fields.Integer(dump_only=True, dump_default=0)

    # Company specific fields (nullable if individual)
    company_name = fields.String(validate=validate.Length(max=100))
    # business_license_number: Sensitive, maybe only shown partially or not at all
    # business_license_photo_url: Sensitive, not exposed
    company_address = fields.String(validate=validate.Length(max=200))
    company_description = fields.String(validate=validate.Length(max=2000))

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # user = fields.Nested(UserSchema(only=("uuid", "phone_number", "status")), dump_only=True)

    class Meta:
        ordered = True

class EmployerProfileUpdateSchema(ma.Schema):
    # Allow updating specific fields
    # profile_type is usually fixed after creation/verification
    real_name = fields.String(validate=validate.Length(max=50))
    avatar_url = fields.URL(validate=validate.Length(max=512))
    nickname = fields.String(validate=validate.Length(max=50))
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    contact_phone = fields.String(validate=validate.Length(max=20))
    # Company specific fields
    company_name = fields.String(validate=validate.Length(max=100))
    company_address = fields.String(validate=validate.Length(max=200))
    company_description = fields.String(validate=validate.Length(max=2000))

    @validates_schema
    def check_at_least_one_field(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided for update.")

    @validates_schema
    def check_company_fields(self, data, **kwargs):
        # This validation depends on knowing the existing profile_type,
        # better handled in the service layer.
        # Example: if profile_type is 'individual', company fields shouldn't be updated.
        pass
