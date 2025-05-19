"""Order, Payment, and Evaluation Models"""
from ..core.extensions import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
import enum

# --- Enums for Order ---
class OrderStatusEnum(enum.Enum):
    pending_start = 'pending_start'
    in_progress = 'in_progress'
    pending_confirmation = 'pending_confirmation'
    completed = 'completed'
    disputed = 'disputed'
    cancelled = 'cancelled'

class ConfirmationStatusEnum(enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    disputed = 'disputed'

class CancellationPartyEnum(enum.Enum):
    freelancer = 'freelancer'
    employer = 'employer'
    platform = 'platform'

# --- Order Model ---
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='订单唯一ID')
    job_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('jobs.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='关联的工作ID')
    application_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('job_applications.id', ondelete='SET NULL', onupdate='CASCADE'), unique=True, nullable=True, comment='关联的申请ID')
    freelancer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='零工用户ID')
    employer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='雇主用户ID')
    order_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='订单金额')
    platform_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, comment='平台服务费')
    freelancer_income = db.Column(db.Numeric(10, 2), nullable=False, comment='零工实际收入')

    start_time_scheduled = db.Column(db.DateTime(timezone=True), nullable=False, comment='计划开始时间')
    end_time_scheduled = db.Column(db.DateTime(timezone=True), nullable=False, comment='计划结束时间')
    start_time_actual = db.Column(db.DateTime(timezone=True), nullable=True, comment='实际开始时间')
    end_time_actual = db.Column(db.DateTime(timezone=True), nullable=True, comment='实际结束时间')
    work_duration_actual = db.Column(db.Numeric(10, 2), nullable=True, comment='实际工时')

    status = db.Column(db.Enum('pending_start', 'in_progress', 'pending_confirmation', 'completed', 'disputed', 'cancelled'), nullable=False, default='pending_start', index=True, comment='订单状态')
    freelancer_confirmation_status = db.Column(db.Enum('pending', 'confirmed', 'disputed'), nullable=False, default='pending', comment='零工确认状态')
    employer_confirmation_status = db.Column(db.Enum('pending', 'confirmed', 'disputed'), nullable=False, default='pending', comment='雇主确认状态')
    confirmation_deadline = db.Column(db.DateTime(timezone=True), nullable=True, comment='确认截止时间')

    cancellation_reason = db.Column(db.Text, nullable=True, comment='取消原因')
    cancelled_by = db.Column(db.Enum('freelancer', 'employer', 'platform'), nullable=True, comment='取消方')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    job = db.relationship('Job', back_populates='orders')
    application = db.relationship('JobApplication', back_populates='order')
    freelancer = db.relationship('User', back_populates='orders_as_freelancer', foreign_keys=[freelancer_user_id])
    employer = db.relationship('User', back_populates='orders_as_employer', foreign_keys=[employer_user_id])
    payments = db.relationship('Payment', back_populates='order', lazy='dynamic') # RESTRICT handled by DB
    evaluations = db.relationship('Evaluation', back_populates='order', cascade='all, delete-orphan', lazy='dynamic')
    wallet_transactions = db.relationship('WalletTransaction', back_populates='order', lazy='dynamic') # SET NULL handled by DB
    dispute = db.relationship('Dispute', back_populates='order', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id} (Job: {self.job_id})>'

# --- Enums for Payment ---
class PaymentStatusEnum(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    succeeded = 'succeeded'
    failed = 'failed'
    refund_pending = 'refund_pending'
    refunded = 'refunded'

# --- Payment Model ---
class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='支付记录唯一ID')
    order_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('orders.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='关联的订单ID')
    payer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='支付方用户ID')
    payee_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False, index=True, comment='收款方用户ID')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='支付金额')
    payment_method = db.Column(db.String(50), nullable=True, comment='支付方式')
    external_transaction_id = db.Column(db.String(128), unique=True, nullable=True, index=True, comment='第三方支付平台流水号')
    internal_transaction_id = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='平台内部交易流水号')
    status = db.Column(db.Enum('pending', 'processing', 'succeeded', 'failed', 'refund_pending', 'refunded'), nullable=False, default='pending', index=True, comment='支付状态')
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='支付成功时间')
    refund_amount = db.Column(db.Numeric(10, 2), nullable=True, comment='退款金额')
    refunded_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='退款成功时间')
    error_code = db.Column(db.String(50), nullable=True, comment='错误码')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    order = db.relationship('Order', back_populates='payments')
    payer = db.relationship('User', back_populates='payments_made', foreign_keys=[payer_user_id])
    payee = db.relationship('User', back_populates='payments_received', foreign_keys=[payee_user_id])
    wallet_transactions = db.relationship('WalletTransaction', back_populates='payment', lazy='dynamic') # SET NULL handled by DB

    def __repr__(self):
        return f'<Payment {self.id} (Order: {self.order_id}, Amount: {self.amount})>'

# --- Enums for Evaluation ---
class EvaluatorRoleEnum(enum.Enum):
    freelancer = 'freelancer'
    employer = 'employer'

# --- Evaluation Model ---
class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='评价唯一ID')
    order_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='关联的订单ID')
    job_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('jobs.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='关联的工作ID (冗余)')
    evaluator_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='评价者用户ID')
    evaluatee_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='被评价者用户ID')
    evaluator_role = db.Column(db.Enum(EvaluatorRoleEnum), nullable=False, comment='评价者角色')
    rating = db.Column(db.SmallInteger, nullable=False, comment='评分 (1-5)')
    comment = db.Column(db.Text, nullable=True, comment='评价内容')
    tags = db.Column(JSON, nullable=True, comment='评价标签 (JSON 数组)')
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False, comment='是否匿名')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    order = db.relationship('Order', back_populates='evaluations')
    job = db.relationship('Job', back_populates='evaluations') # Redundant FK
    evaluator = db.relationship('User', back_populates='evaluations_given', foreign_keys=[evaluator_user_id])
    evaluatee = db.relationship('User', back_populates='evaluations_received', foreign_keys=[evaluatee_user_id])

    # --- Constraints ---
    __table_args__ = (db.UniqueConstraint('order_id', 'evaluator_user_id', name='uq_order_evaluator'),)

    def __repr__(self):
        return f'<Evaluation {self.id} (Order: {self.order_id}, Evaluator: {self.evaluator_user_id})>'
