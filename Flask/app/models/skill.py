"""Skill Models"""
from ..core.extensions import db
from datetime import datetime
import enum

# --- Skill Model ---
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='技能唯一ID')
    name = db.Column(db.String(50), nullable=False, unique=True, comment='技能名称')
    category = db.Column(db.String(50), nullable=True, index=True, comment='技能分类')
    description = db.Column(db.Text, nullable=True, comment='技能描述')
    is_hot = db.Column(db.Boolean, nullable=False, default=False, index=True, comment='是否热门技能')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    freelancers_assoc = db.relationship('FreelancerSkill', back_populates='skill', cascade='all, delete-orphan')
    jobs_required_assoc = db.relationship('JobRequiredSkill', back_populates='skill', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Skill {self.id} ({self.name})>'

# --- Enums for FreelancerSkill ---
class ProficiencyLevelEnum(enum.Enum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    advanced = 'advanced'
    expert = 'expert'

# --- FreelancerSkill Association Model ---
class FreelancerSkill(db.Model):
    __tablename__ = 'freelancer_skills'

    freelancer_user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, comment='零工用户ID')
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True, comment='技能ID')
    proficiency_level = db.Column(db.Enum(ProficiencyLevelEnum), nullable=True, comment='熟练度')
    years_of_experience = db.Column(db.SmallInteger, nullable=True, comment='相关经验年限')
    certificate_url = db.Column(db.String(512), nullable=True, comment='相关技能证书 URL')
    certificate_verified = db.Column(db.Boolean, nullable=False, default=False, comment='证书是否已由平台认证审核')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    freelancer = db.relationship('User', back_populates='freelancer_skills_assoc')
    skill = db.relationship('Skill', back_populates='freelancers_assoc')

    def __repr__(self):
        return f'<FreelancerSkill (User: {self.freelancer_user_id}, Skill: {self.skill_id})>'

# --- JobRequiredSkill Association Model ---
class JobRequiredSkill(db.Model):
    __tablename__ = 'job_required_skills'

    job_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('jobs.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, comment='工作ID')
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True, comment='技能ID')
    is_mandatory = db.Column(db.Boolean, nullable=False, default=True, comment='是否必须具备的技能')

    # --- Relationships ---
    job = db.relationship('Job', back_populates='required_skills_assoc')
    skill = db.relationship('Skill', back_populates='jobs_required_assoc')

    def __repr__(self):
        return f'<JobRequiredSkill (Job: {self.job_id}, Skill: {self.skill_id})>'
