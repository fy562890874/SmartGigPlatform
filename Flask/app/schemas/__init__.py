# Schemas initialization
from .user_schema import (
    UserSchema,
    UserPublicSchema,
    UserRegistrationSchema,
    UserLoginSchema,
    UserProfileUpdateSchema
)
from .admin_schema import (
    AdminUserSchema,
    AdminUserUpdateSchema,
    AdminUserLoginSchema
)
from .dispute_schema import (
    DisputeSchema,
    DisputeCreateSchema,
    DisputeUpdateSchema
)
from .favorite_schema import (
    FavoriteSchema,
    FavoriteCreateSchema,
    FavoriteListSchema
)
from .job_schema import (
    JobSchema,
    JobCreateSchema,
    JobUpdateSchema,
    JobApplicationSchema,
    JobApplicationCreateSchema,
    JobApplicationUpdateSchema,
    JobApplicationCancelSchema,
    JobRequiredSkillSchema
)
from .message_schema import (
    MessageSchema,
    MessageCreateSchema,
    MessageMarkReadSchema
)
from .notification_schema import (
    NotificationSchema,
    NotificationMarkReadSchema,
    NotificationCreateSchema
)
from .order_schema import (
    OrderSchema,
    OrderActionSchema,
    OrderTimeUpdateSchema,
    EvaluationSchema,
    EvaluationCreateSchema
)
from .profile_schema import (
    FreelancerProfileSchema,
    FreelancerProfileUpdateSchema,
    EmployerProfileSchema,
    EmployerProfileUpdateSchema
)
from .report_schema import (
    ReportSchema,
    ReportCreateSchema,
    ReportUpdateSchema
)
from .skill_schema import (
    SkillSchema,
    SkillCreateSchema,
    SkillUpdateSchema,
    FreelancerSkillSchema,
    FreelancerSkillCreateSchema,
    FreelancerSkillUpdateSchema
)
from .system_schema import (
    SystemConfigSchema,
    SystemConfigUpdateSchema
)
from .verification_schema import (
    VerificationRecordSchema,
    VerificationRecordCreateSchema,
    VerificationRecordReviewSchema
)
from .wallet_schema import (
    WithdrawalRequestSchema,
    WithdrawalRequestCreateSchema,
    WithdrawalRequestUpdateSchema,
    WalletTransactionSchema,
    UserWalletSchema
)

# You can create instances here if needed globally, or import the classes directly
# user_schema = UserSchema()
# users_schema = UserSchema(many=True)
# ... etc.
