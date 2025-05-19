"""Wallet Related Models"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON

# --- Enums for WithdrawalRequest ---
class WithdrawalStatusEnum(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    succeeded = 'succeeded'
    failed = 'failed'
    cancelled = 'cancelled'

# --- WithdrawalRequest Model ---
class WithdrawalRequest(db.Model):
    __tablename__ = 'withdrawal_requests'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='提现申请ID')
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='申请用户ID')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='申请提现金额')
    withdrawal_method = db.Column(db.String(50), nullable=False, comment='提现方式')
    account_info = db.Column(JSON, nullable=False, comment='提现账户信息 (JSON)')
    status = db.Column(db.Enum(WithdrawalStatusEnum), nullable=False, default=WithdrawalStatusEnum.pending, index=True, comment='申请状态')
    platform_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, comment='提现手续费')
    actual_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='实际到账金额')
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='后台处理时间')
    external_transaction_id = db.Column(db.String(128), unique=True, nullable=True, index=True, comment='外部转账流水号')
    failure_reason = db.Column(db.Text, nullable=True, comment='失败原因')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    user = db.relationship('User', back_populates='withdrawal_requests')
    wallet_transactions = db.relationship('WalletTransaction', back_populates='withdrawal_request', lazy='dynamic')

    def __repr__(self):
        return f'<WithdrawalRequest {self.id} (User: {self.user_id}, Amount: {self.amount}, Status: {self.status.name})>'

# --- Enums for WalletTransaction ---
class TransactionTypeEnum(enum.Enum):
    deposit = 'deposit'
    withdrawal = 'withdrawal'
    income = 'income'
    payment = 'payment'
    refund = 'refund'
    platform_fee = 'platform_fee'
    adjustment = 'adjustment'

# --- WalletTransaction Model ---
class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='流水唯一ID')
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='关联用户ID')
    transaction_type = db.Column(db.Enum(TransactionTypeEnum), nullable=False, index=True, comment='交易类型')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='交易金额 (正增负减)')
    balance_after = db.Column(db.Numeric(10, 2), nullable=False, comment='本次交易后该用户的钱包余额快照')
    related_payment_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('payments.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='关联的支付记录ID')
    related_order_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('orders.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='关联的订单ID (冗余)')
    related_withdrawal_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('withdrawal_requests.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True, index=True, comment='关联的提现申请ID')
    description = db.Column(db.String(255), nullable=True, comment='交易描述')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # --- Relationships ---
    user = db.relationship('User', back_populates='wallet_transactions')
    payment = db.relationship('Payment', back_populates='wallet_transactions')
    order = db.relationship('Order', back_populates='wallet_transactions') # Redundant FK
    withdrawal_request = db.relationship('WithdrawalRequest', back_populates='wallet_transactions')

    def __repr__(self):
        return f'<WalletTransaction {self.id} (User: {self.user_id}, Type: {self.transaction_type.name}, Amount: {self.amount})>'

# --- UserWallet Model ---
class UserWallet(db.Model):
    __tablename__ = 'user_wallets'

    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, comment='关联用户ID')
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, comment='当前可用余额')
    frozen_balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, comment='冻结金额')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    user = db.relationship('User', back_populates='wallet')

    def __repr__(self):
        return f'<UserWallet for User {self.user_id} (Balance: {self.balance})>'
