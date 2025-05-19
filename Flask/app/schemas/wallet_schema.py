"""Wallet Related Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from ..models.wallet import WithdrawalStatusEnum, TransactionTypeEnum

# Basic Schemas for Nesting
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)

class PaymentBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)

class OrderBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)


# --- Withdrawal Request Schema ---
class WithdrawalRequestSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True) # Set from JWT
    amount = fields.Decimal(places=2, as_string=True, required=True, validate=validate.Range(min=1.00)) # Example: min withdrawal amount
    withdrawal_method = fields.String(required=True, validate=validate.Length(max=50)) # e.g., 'alipay', 'bank_transfer'
    account_info = fields.Dict(required=True) # JSON field, structure depends on method
    status = fields.String(validate=validate.OneOf([e.value for e in WithdrawalStatusEnum]), dump_only=True, dump_default=WithdrawalStatusEnum.pending.value)
    platform_fee = fields.Decimal(places=2, as_string=True, dump_only=True) # Calculated by system
    actual_amount = fields.Decimal(places=2, as_string=True, dump_only=True) # Calculated by system
    processed_at = fields.DateTime(dump_only=True)
    external_transaction_id = fields.String(dump_only=True)
    failure_reason = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    user = fields.Nested(UserBasicSchema, dump_only=True)

    class Meta:
        ordered = True

class WithdrawalRequestCreateSchema(ma.Schema):
    amount = fields.Decimal(places=2, as_string=True, required=True, validate=validate.Range(min=1.00))
    withdrawal_method = fields.String(required=True, validate=validate.OneOf(['alipay', 'bank_transfer'])) # Example methods
    account_info = fields.Dict(required=True)

    @validates_schema
    def validate_account_info(self, data, **kwargs):
        method = data.get('withdrawal_method')
        info = data.get('account_info')
        if not method or not info:
            return # Handled by required=True

        if method == 'alipay':
            required_keys = ['account', 'real_name']
            if not all(key in info for key in required_keys):
                raise ValidationError(f"Alipay requires keys: {required_keys}", "account_info")
        elif method == 'bank_transfer':
            required_keys = ['card_number', 'bank_name', 'branch_name', 'real_name']
            if not all(key in info for key in required_keys):
                 raise ValidationError(f"Bank transfer requires keys: {required_keys}", "account_info")
        # Add more validation for specific formats if needed


class WithdrawalRequestUpdateSchema(ma.Schema): # For Admin processing
    status = fields.String(required=True, validate=validate.OneOf([
        WithdrawalStatusEnum.processing.value,
        WithdrawalStatusEnum.succeeded.value,
        WithdrawalStatusEnum.failed.value,
        WithdrawalStatusEnum.cancelled.value # Maybe admin can cancel?
    ]))
    external_transaction_id = fields.String(validate=validate.Length(max=128))
    failure_reason = fields.String(validate=validate.Length(max=500))

    @validates_schema
    def validate_update_fields(self, data, **kwargs):
        status = data.get('status')
        txn_id = data.get('external_transaction_id')
        reason = data.get('failure_reason')

        if status == WithdrawalStatusEnum.succeeded.value and not txn_id:
            raise ValidationError("External transaction ID is required for succeeded status.", "external_transaction_id")
        if status == WithdrawalStatusEnum.failed.value and not reason:
            raise ValidationError("Failure reason is required for failed status.", "failure_reason")
        if status != WithdrawalStatusEnum.failed.value and reason:
            raise ValidationError("Failure reason should only be provided for failed status.", "failure_reason")
        if status != WithdrawalStatusEnum.succeeded.value and txn_id:
             raise ValidationError("External transaction ID should only be provided for succeeded status.", "external_transaction_id")


# --- Wallet Transaction Schema ---
class WalletTransactionSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    transaction_type = fields.String(validate=validate.OneOf([e.value for e in TransactionTypeEnum]), dump_only=True)
    amount = fields.Decimal(places=2, as_string=True, dump_only=True) # Positive or negative
    balance_after = fields.Decimal(places=2, as_string=True, dump_only=True)
    related_payment_id = fields.Integer(dump_only=True, allow_none=True)
    related_order_id = fields.Integer(dump_only=True, allow_none=True)
    related_withdrawal_id = fields.Integer(dump_only=True, allow_none=True)
    description = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # Relationships (dump only, basic info)
    user = fields.Nested(UserBasicSchema, dump_only=True)
    payment = fields.Nested(PaymentBasicSchema, dump_only=True)
    order = fields.Nested(OrderBasicSchema, dump_only=True)
    withdrawal_request = fields.Nested(lambda: WithdrawalRequestSchema(only=("id", "status")), dump_only=True) # Avoid full cycle

    class Meta:
        ordered = True


# --- User Wallet Schema ---
class UserWalletSchema(ma.Schema):
    user_id = fields.Integer(dump_only=True)
    balance = fields.Decimal(places=2, as_string=True, dump_only=True)
    frozen_balance = fields.Decimal(places=2, as_string=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        ordered = True

# No Create/Update for WalletTransaction or UserWallet usually, they are managed internally by services.
