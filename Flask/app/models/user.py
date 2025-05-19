"""User Model"""
from ..core.extensions import db
from datetime import datetime
import enum
import uuid
from sqlalchemy.dialects.mysql import JSON
from ..core.extensions import bcrypt

# Define Enums based on createDB.sql
class UserRoleEnum(enum.Enum):
    freelancer = 'freelancer'
    employer = 'employer'

class UserStatusEnum(enum.Enum):
    pending_verification = 'pending_verification'
    active = 'active'
    inactive = 'inactive'
    banned = 'banned'

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='用户唯一ID') # Use BigInteger for MySQL
    # Add UUID field
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), comment='对外暴露的用户UUID')

    phone_number = db.Column(db.String(20), nullable=False, unique=True, comment='手机号 (主要登录凭证)')
    password_hash = db.Column(db.String(255), nullable=False, comment='哈希后的密码') # Length adjusted
    email = db.Column(db.String(100), unique=True, nullable=True, index=True, comment='邮箱 (可选登录或通知方式)')
    wechat_openid = db.Column(db.String(128), unique=True, nullable=True, index=True, comment='微信 OpenID (用于微信登录)')
    alipay_userid = db.Column(db.String(128), unique=True, nullable=True, index=True, comment='支付宝 UserID (用于支付宝登录)')

    # Replace user_type with current_role and available_roles
    # user_type = db.Column(db.Enum(UserTypeEnum), nullable=False, comment='用户类型')
    current_role = db.Column(db.Enum('freelancer', 'employer'), nullable=False, default='freelancer', comment='用户当前活跃角色')
    available_roles = db.Column(JSON, nullable=False, comment='用户拥有的角色列表, e.g., ["freelancer", "employer"]')

    status = db.Column(db.Enum('pending_verification', 'active', 'inactive', 'banned'), nullable=False, default='pending_verification', index=True, comment='账号状态')
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='最后登录时间')
    registered_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True, comment='注册时间')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    # One-to-One
    freelancer_profile = db.relationship('FreelancerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    employer_profile = db.relationship('EmployerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    wallet = db.relationship('UserWallet', back_populates='user', uselist=False, cascade='all, delete-orphan')

    # One-to-Many (Jobs posted by employer)
    jobs_posted = db.relationship('Job', back_populates='employer', foreign_keys='Job.employer_user_id', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Applications made by freelancer)
    job_applications_made = db.relationship('JobApplication', back_populates='freelancer', foreign_keys='JobApplication.freelancer_user_id', lazy='dynamic', cascade='all, delete-orphan')
    # One-to-Many (Applications received by employer for their jobs - redundant but potentially useful)
    job_applications_received = db.relationship('JobApplication', back_populates='employer', foreign_keys='JobApplication.employer_user_id', lazy='dynamic', cascade='all, delete-orphan') # employer_user_id is redundant in JobApplication

    # One-to-Many (Orders where user is freelancer)
    orders_as_freelancer = db.relationship('Order', back_populates='freelancer', foreign_keys='Order.freelancer_user_id', lazy='dynamic') # RESTRICT handled by DB
    # One-to-Many (Orders where user is employer)
    orders_as_employer = db.relationship('Order', back_populates='employer', foreign_keys='Order.employer_user_id', lazy='dynamic') # RESTRICT handled by DB

    # One-to-Many (Payments made by user)
    payments_made = db.relationship('Payment', back_populates='payer', foreign_keys='Payment.payer_user_id', lazy='dynamic') # RESTRICT handled by DB
    # One-to-Many (Payments received by user)
    payments_received = db.relationship('Payment', back_populates='payee', foreign_keys='Payment.payee_user_id', lazy='dynamic') # RESTRICT handled by DB

    # One-to-Many (Evaluations given by user)
    evaluations_given = db.relationship('Evaluation', back_populates='evaluator', foreign_keys='Evaluation.evaluator_user_id', lazy='dynamic', cascade='all, delete-orphan')
    # One-to-Many (Evaluations received by user)
    evaluations_received = db.relationship('Evaluation', back_populates='evaluatee', foreign_keys='Evaluation.evaluatee_user_id', lazy='dynamic', cascade='all, delete-orphan')

    # Many-to-Many (Skills for freelancer) - through association object
    freelancer_skills_assoc = db.relationship('FreelancerSkill', back_populates='freelancer', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Messages sent by user)
    messages_sent = db.relationship('Message', back_populates='sender', foreign_keys='Message.sender_id', lazy='dynamic') # SET NULL handled by DB
    # One-to-Many (Messages received by user)
    messages_received = db.relationship('Message', back_populates='recipient', foreign_keys='Message.recipient_id', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Verification records submitted by user)
    verification_records = db.relationship('VerificationRecord', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Withdrawal requests made by user)
    withdrawal_requests = db.relationship('WithdrawalRequest', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Wallet transactions for user)
    wallet_transactions = db.relationship('WalletTransaction', back_populates='user', lazy='dynamic') # RESTRICT handled by DB

    # One-to-Many (Notifications for user)
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Favorites made by user)
    favorites = db.relationship('Favorite', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Reports made by user)
    reports_made = db.relationship('Report', back_populates='reporter', foreign_keys='Report.reporter_user_id', lazy='dynamic', cascade='all, delete-orphan')

    # One-to-Many (Disputes initiated by user)
    disputes_initiated = db.relationship('Dispute', back_populates='initiator', foreign_keys='Dispute.initiator_user_id', lazy='dynamic', cascade='all, delete-orphan')


    def __repr__(self):
        return f'<User {self.id} ({self.phone_number})>'

    # Helper property to get skills directly
    @property
    def skills(self):
        return [assoc.skill for assoc in self.freelancer_skills_assoc]

    # Add methods for password hashing/checking if not handled solely in service layer
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
