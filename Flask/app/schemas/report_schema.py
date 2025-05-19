"""Report Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError, validates
from ..models.report import ReportTypeEnum, ReportStatusEnum

# Basic Schemas for Nesting
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)

class AdminUserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(dump_only=True)

class ReportSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    reporter_user_id = fields.Integer(dump_only=True) # Set from JWT
    report_type = fields.String(required=True, validate=validate.OneOf([e.value for e in ReportTypeEnum]))
    target_id = fields.Integer(required=True)
    reason_category = fields.String(required=True, validate=validate.Length(max=50)) # Maybe use Enum validation if categories are fixed
    reason_description = fields.String(validate=validate.Length(max=1000))
    attachments = fields.List(fields.URL(), description="List of evidence attachment URLs")
    status = fields.String(validate=validate.OneOf([e.value for e in ReportStatusEnum]), dump_only=True, dump_default=ReportStatusEnum.pending.value)
    processor_id = fields.Integer(dump_only=True)
    processed_at = fields.DateTime(dump_only=True)
    processing_result = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    reporter = fields.Nested(UserBasicSchema, dump_only=True, attribute="reporter_user")
    processor = fields.Nested(AdminUserBasicSchema, dump_only=True)
    # Target object could be nested dynamically based on report_type, but might be complex/costly.
    # Often just returning target_id and report_type is sufficient for list/detail views.

    class Meta:
        ordered = True

class ReportCreateSchema(ma.Schema):
    report_type = fields.String(required=True, validate=validate.OneOf([e.value for e in ReportTypeEnum]))
    target_id = fields.Integer(required=True)
    reason_category = fields.String(required=True, validate=validate.Length(min=3, max=50))
    reason_description = fields.String(validate=validate.Length(max=1000))
    attachments = fields.List(fields.URL(), description="List of evidence attachment URLs")

    @validates('target_id')
    def validate_target_id(self, value):
        if value <= 0:
            raise ValidationError("target_id must be a positive integer.")

class ReportUpdateSchema(ma.Schema): # For Admin processing
    status = fields.String(required=True, validate=validate.OneOf([e.value for e in ReportStatusEnum if e != ReportStatusEnum.pending])) # Cannot set back to pending
    processing_result = fields.String(required=True, validate=validate.Length(min=5, max=1000))

    @validates_schema
    def validate_status_result(self, data, **kwargs):
        status = data.get('status')
        result = data.get('processing_result')
        # Add logic if specific results are needed for certain statuses
        if not status or not result:
             raise ValidationError("Both status and processing_result are required.")

