"""Models Initialization"""
# Import all models here to make them accessible via app.models.<ModelName>
# Also ensures SQLAlchemy detects them for migrations.

from app.core.extensions import db

from .user import User
from .profile import FreelancerProfile, EmployerProfile
from .job import Job, JobApplication
from .order import Order, Payment, Evaluation
from .skill import Skill, FreelancerSkill, JobRequiredSkill
from .message import Message
from .admin import AdminUser
from .verification import VerificationRecord
from .wallet import WithdrawalRequest, WalletTransaction, UserWallet
from .notification import Notification
from .favorite import Favorite
from .report import Report
from .dispute import Dispute
from .system import SystemConfig

# You can optionally define __all__ for explicit exports
__all__ = [
    'User',
    'FreelancerProfile',
    'EmployerProfile',
    'Job',
    'JobApplication',
    'Order',
    'Payment',
    'Evaluation',
    'Skill',
    'FreelancerSkill',
    'JobRequiredSkill',
    'Message',
    'AdminUser',
    'VerificationRecord',
    'WithdrawalRequest',
    'WalletTransaction',
    'UserWallet',
    'Notification',
    'Favorite',
    'Report',
    'Dispute',
    'SystemConfig',
]

