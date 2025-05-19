"""Order and Evaluation Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from ..models.order import OrderStatusEnum, ConfirmationStatusEnum, CancellationPartyEnum
from .user_schema import UserSchema # Assuming full UserSchema exists
from .job_schema import JobSchema # Assuming full JobSchema exists
from .job_schema import JobApplicationSchema # Assuming full JobApplicationSchema exists

# --- Basic Schemas for Nesting ---
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)
    avatar_url = fields.URL(dump_only=True)

class JobBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)

class JobApplicationBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)


# --- Evaluation Schema ---
class EvaluationSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    order_id = fields.Integer(required=True) # Context for creation
    job_id = fields.Integer(dump_only=True) # Redundant, from order
    evaluator_user_id = fields.Integer(dump_only=True) # Set from JWT
    evaluatee_user_id = fields.Integer(dump_only=True) # Derived from order/context
    evaluator_role = fields.String(dump_only=True) # Derived from context
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.String(validate=validate.Length(max=1000))
    tags = fields.List(fields.String(validate=validate.Length(max=30)))
    is_anonymous = fields.Boolean(dump_default=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    # Avoid nesting order/job back to prevent cycles if possible
    evaluator = fields.Nested(UserBasicSchema, dump_only=True, attribute="evaluator_user")
    evaluatee = fields.Nested(UserBasicSchema, dump_only=True, attribute="evaluatee_user")

    class Meta:
        ordered = True

class EvaluationCreateSchema(ma.Schema):
    # order_id is usually part of the URL endpoint, e.g., /orders/{order_id}/evaluations
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.String(validate=validate.Length(max=1000))
    tags = fields.List(fields.String(validate=validate.Length(max=30)))
    is_anonymous = fields.Boolean(dump_default=False)


# --- Order Schema ---
class OrderSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    job_id = fields.Integer(dump_only=True) # Derived from application or job context
    application_id = fields.Integer(dump_only=True, allow_none=True) # Set on creation from application
    freelancer_user_id = fields.Integer(dump_only=True)
    employer_user_id = fields.Integer(dump_only=True)

    order_amount = fields.Decimal(places=2, as_string=True, dump_only=True) # Calculated by service
    platform_fee = fields.Decimal(places=2, as_string=True, dump_only=True) # Calculated by service
    freelancer_income = fields.Decimal(places=2, as_string=True, dump_only=True) # Calculated by service

    start_time_scheduled = fields.DateTime(dump_only=True) # From Job or Application agreement
    end_time_scheduled = fields.DateTime(dump_only=True) # From Job or Application agreement
    start_time_actual = fields.DateTime(allow_none=True) # Updated via action
    end_time_actual = fields.DateTime(allow_none=True) # Updated via action
    work_duration_actual = fields.Decimal(places=2, as_string=True, dump_only=True, allow_none=True) # Calculated

    status = fields.String(validate=validate.OneOf([e.value for e in OrderStatusEnum]), dump_only=True)
    freelancer_confirmation_status = fields.String(validate=validate.OneOf([e.value for e in ConfirmationStatusEnum]), dump_only=True)
    employer_confirmation_status = fields.String(validate=validate.OneOf([e.value for e in ConfirmationStatusEnum]), dump_only=True)
    confirmation_deadline = fields.DateTime(dump_only=True, allow_none=True)

    cancellation_reason = fields.String(dump_only=True, allow_none=True)
    cancelled_by = fields.String(validate=validate.OneOf([e.value for e in CancellationPartyEnum]), dump_only=True, allow_none=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    job = fields.Nested(JobBasicSchema, dump_only=True)
    application = fields.Nested(JobApplicationBasicSchema, dump_only=True)
    freelancer = fields.Nested(UserBasicSchema, dump_only=True, attribute="freelancer_user")
    employer = fields.Nested(UserBasicSchema, dump_only=True, attribute="employer_user")
    # evaluations = fields.Nested(EvaluationSchema, many=True, dump_only=True) # Maybe load evaluations separately

    class Meta:
        ordered = True

# Schema for creating an order (usually internal, triggered by application acceptance)
# class OrderCreateSchema(ma.Schema):
#     application_id = fields.Integer(required=True) # Trigger based on this

# Schema for updating order status (e.g., start, complete, confirm)
class OrderActionSchema(ma.Schema):
    action = fields.String(required=True, validate=validate.OneOf([
        'start_work',         # Freelancer starts
        'complete_work',      # Freelancer completes
        'confirm_completion', # Employer confirms
        'dispute_completion', # Employer disputes
        'cancel_order'        # Either party (before start?) or Platform
    ]))
    # Optional fields depending on action
    cancellation_reason = fields.String(validate=validate.Length(max=500)) # Required if action is 'cancel_order' by user

    @validates_schema
    def validate_cancel_reason(self, data, **kwargs):
        if data.get('action') == 'cancel_order' and not data.get('cancellation_reason'):
             # Cancellation reason might be mandatory depending on who cancels and when
             # raise ValidationError("Cancellation reason is required.", "cancellation_reason")
             pass

# Schema for updating actual times (potentially part of 'complete_work' or separate)
class OrderTimeUpdateSchema(ma.Schema):
    start_time_actual = fields.DateTime(required=True)
    end_time_actual = fields.DateTime(required=True)

    @validates_schema
    def validate_times(self, data, **kwargs):
        if data['start_time_actual'] >= data['end_time_actual']:
            raise ValidationError("Actual end time must be after actual start time.", "end_time_actual")

