"""Admin User Model"""
from ..core.extensions import db
from datetime import datetime
import enum

# --- Enums for AdminUser ---
class AdminStatusEnum(enum.Enum):
    active = 'active'
    inactive = 'inactive'

# --- AdminUser Model ---
class AdminUser(db.Model):
    __tablename__ = 'admin_users'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, comment='管理员登录账号')
    password_hash = db.Column(db.String(255), nullable=False, comment='哈希后的密码')
    real_name = db.Column(db.String(50), nullable=True, comment='真实姓名')
    role = db.Column(db.String(50), nullable=False, comment='管理员角色')
    status = db.Column(db.Enum(AdminStatusEnum), nullable=False, default=AdminStatusEnum.active, comment='账号状态')
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    # Relationships to records this admin processed (e.g., verifications, reports, disputes)
    reviewed_verifications = db.relationship('VerificationRecord', back_populates='reviewer', lazy='dynamic')
    processed_reports = db.relationship('Report', back_populates='processor', lazy='dynamic')
    mediated_disputes = db.relationship('Dispute', back_populates='platform_mediator', lazy='dynamic')


    def __repr__(self):
        return f'<AdminUser {self.id} ({self.username})>'

    # Add password methods if needed
    # def set_password(self, password):
    #     self.password_hash = generate_password_hash(password)
    #
    # def check_password(self, password):
    #     return check_password_hash(self.password_hash, password)
