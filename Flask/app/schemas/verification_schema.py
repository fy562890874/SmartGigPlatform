"""Verification Record Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema
from ..models.verification import VerificationProfileTypeEnum, VerificationRecordStatusEnum # 修正枚举导入

# Basic Schemas for Nesting
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)

class AdminUserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(dump_only=True)


class VerificationRecordSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True) # Associated user
    profile_type = fields.String(required=True, validate=validate.OneOf([e.value for e in VerificationProfileTypeEnum]))
    submitted_data = fields.Dict(required=True) # JSON field, structure depends on profile_type
    status = fields.String(validate=validate.OneOf([e.value for e in VerificationRecordStatusEnum]), dump_only=True, dump_default=VerificationRecordStatusEnum.pending.value)
    reviewer_id = fields.Integer(dump_only=True)
    reviewed_at = fields.DateTime(dump_only=True)
    rejection_reason = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    user = fields.Nested(UserBasicSchema, dump_only=True)
    reviewer = fields.Nested(AdminUserBasicSchema, dump_only=True)

    class Meta:
        ordered = True

class VerificationRecordCreateSchema(ma.Schema):
    # user_id is set from JWT/context
    profile_type = fields.String(required=True, validate=validate.OneOf([e.value for e in VerificationProfileTypeEnum]))
    # submitted_data structure needs validation based on profile_type
    # This might require a custom validation method or different schemas per type
    submitted_data = fields.Dict(required=True)

    @validates_schema
    def validate_submitted_data(self, data, **kwargs):
        profile_type = data.get('profile_type')
        submitted_data = data.get('submitted_data')
        if not profile_type or not submitted_data:
            return # Handled by required=True

        if profile_type == VerificationProfileTypeEnum.freelancer.value:
            # Check for required fields like real_name, id_card_number, id_card_photo_front, id_card_photo_back
            required_keys = ['real_name', 'id_card_number', 'id_card_photo_front', 'id_card_photo_back']
            if not all(key in submitted_data for key in required_keys):
                raise validate.ValidationError(f"Missing required fields for freelancer verification: {required_keys}")
        elif profile_type == VerificationProfileTypeEnum.employer_individual.value:
             # Similar check for individual employer
            required_keys = ['real_name', 'id_card_number', 'id_card_photo_front', 'id_card_photo_back']
            if not all(key in submitted_data for key in required_keys):
                raise validate.ValidationError(f"Missing required fields for individual employer verification: {required_keys}")
        elif profile_type == VerificationProfileTypeEnum.employer_company.value:
             # Check for company fields like company_name, business_license_number, business_license_photo_url, contact_person_name, contact_person_id_card...
            required_keys = ['company_name', 'business_license_number', 'business_license_photo_url'] # Example
            if not all(key in submitted_data for key in required_keys):
                 raise validate.ValidationError(f"Missing required fields for company verification: {required_keys}")
        # Add more specific validation for data formats (e.g., ID card number format) if needed


class VerificationRecordReviewSchema(ma.Schema): # For Admin review action
    status = fields.String(required=True, validate=validate.OneOf([
        VerificationRecordStatusEnum.approved.value,
        VerificationRecordStatusEnum.rejected.value
    ]))
    rejection_reason = fields.String(validate=validate.Length(max=500))

    @validates_schema
    def validate_rejection_reason(self, data, **kwargs):
        if data.get('status') == VerificationRecordStatusEnum.rejected.value and not data.get('rejection_reason'):
            raise validate.ValidationError("Rejection reason is required when rejecting a verification.", "rejection_reason")
        if data.get('status') == VerificationRecordStatusEnum.approved.value and data.get('rejection_reason'):
             raise validate.ValidationError("Rejection reason should not be provided when approving a verification.", "rejection_reason")

