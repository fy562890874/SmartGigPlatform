"""Job and Job Application Models"""
from ..core.extensions import db
from datetime import datetime
import enum
from sqlalchemy.dialects.mysql import JSON
# --- Enums for Job ---
class SalaryTypeEnum(enum.Enum):
    hourly = 'hourly'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    fixed = 'fixed'
    negotiable = 'negotiable'

class JobStatusEnum(enum.Enum):
    pending_review = 'pending_review'
    rejected = 'rejected'
    active = 'active'
    filled = 'filled'
    in_progress = 'in_progress'
    completed = 'completed'
    cancelled = 'cancelled'
    expired = 'expired'

# --- Enums for JobApplication ---
class JobApplicationStatusEnum(enum.Enum):
    pending = 'pending'
    viewed = 'viewed'
    accepted = 'accepted'
    rejected = 'rejected'
    cancelled_by_freelancer = 'cancelled_by_freelancer'
    # withdrawn_by_employer = 'withdrawn_by_employer' # Example, if needed
    # interview_scheduled = 'interview_scheduled' # Example, if needed

# --- Job Model ---
class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='工作唯一ID')
    employer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='发布者用户ID')
    title = db.Column(db.String(100), nullable=False, comment='工作标题') # Add index in DB
    description = db.Column(db.Text, nullable=False, comment='工作描述') # Add index in DB
    job_category = db.Column(db.String(50), nullable=False, index=True, comment='工作类别')
    job_tags = db.Column(JSON, nullable=True, comment='工作标签 (JSON 数组)')

    # Replace location with specific fields + point
    # location = db.Column(db.String(200), nullable=False, comment='工作地点')
    location_address = db.Column(db.String(200), nullable=False, comment='详细地址')
    location_province = db.Column(db.String(50), nullable=True, index=True, comment='省份 (冗余)')
    location_city = db.Column(db.String(50), nullable=True, index=True, comment='城市 (冗余)')
    location_district = db.Column(db.String(50), nullable=True, index=True, comment='区县 (冗余)')
    location_point = db.Column(db.JSON, nullable=True, comment='地理坐标 (GeoJSON)') # Add spatial index in DB if supported for JSON

    start_time = db.Column(db.DateTime(timezone=True), nullable=False, comment='预计开始时间')
    end_time = db.Column(db.DateTime(timezone=True), nullable=False, comment='预计结束时间')
    duration_estimate = db.Column(db.Numeric(10, 2), nullable=True, comment='预计工时')

    # Rename salary to salary_amount
    salary_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='薪资金额')
    salary_type = db.Column(db.Enum('hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable'), nullable=False, comment='计薪方式')
    salary_negotiable = db.Column(db.Boolean, nullable=False, default=False, comment='薪资是否可议')

    # Rename required_persons to required_people
    required_people = db.Column(db.Integer, nullable=False, default=1, comment='需求人数')
    accepted_people = db.Column(db.Integer, nullable=False, default=0, comment='已接受人数 (冗余)')

    skill_requirements = db.Column(db.Text, nullable=True, comment='技能要求描述')
    is_urgent = db.Column(db.Boolean, nullable=False, default=False, index=True, comment='是否急聘')

    status = db.Column(db.Enum(JobStatusEnum), nullable=False, default=JobStatusEnum.pending_review, index=True, comment='工作状态')
    cancellation_reason = db.Column(db.Text, nullable=True, comment='取消原因')

    view_count = db.Column(db.Integer, nullable=False, default=0, comment='浏览次数')
    application_deadline = db.Column(db.DateTime(timezone=True), nullable=True, comment='报名截止时间')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    employer = db.relationship('User', back_populates='jobs_posted', foreign_keys=[employer_user_id])
    applications = db.relationship('JobApplication', back_populates='job', cascade='all, delete-orphan', lazy='dynamic')
    orders = db.relationship('Order', back_populates='job', lazy='dynamic') # RESTRICT handled by DB
    evaluations = db.relationship('Evaluation', back_populates='job', cascade='all, delete-orphan', lazy='dynamic')
    required_skills_assoc = db.relationship('JobRequiredSkill', back_populates='job', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Job {self.id} ({self.title})>'


class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True, comment='申请唯一ID')
    job_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('jobs.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='关联的工作ID')
    freelancer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='申请的零工用户ID')
    employer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='工作的发布者用户ID (冗余)')
    apply_message = db.Column(db.Text, nullable=True, comment='申请留言/备注')
    status = db.Column(db.Enum(JobApplicationStatusEnum), nullable=False, default=JobApplicationStatusEnum.pending, index=True, comment='申请状态')
    applied_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True, comment='申请时间')
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True, comment='处理时间')
    rejection_reason = db.Column(db.Text, nullable=True, comment='拒绝原因')

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    job = db.relationship('Job', back_populates='applications')
    freelancer = db.relationship('User', back_populates='job_applications_made', foreign_keys=[freelancer_user_id])
    employer = db.relationship('User', back_populates='job_applications_received', foreign_keys=[employer_user_id]) # Redundant FK
    order = db.relationship('Order', back_populates='application', uselist=False) # One-to-one

    # --- Constraints ---
    __table_args__ = (db.UniqueConstraint('job_id', 'freelancer_user_id', name='uq_job_freelancer_application'),)

    def __repr__(self):
        return f'<JobApplication {self.id} (Job: {self.job_id}, Freelancer: {self.freelancer_user_id})>'
