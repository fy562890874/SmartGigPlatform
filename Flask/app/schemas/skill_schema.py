"""Skill Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate
from ..models.skill import ProficiencyLevelEnum

# --- Skill Schema ---
class SkillSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    category = fields.String(validate=validate.Length(max=50))
    description = fields.String(validate=validate.Length(max=255))
    is_hot = fields.Boolean(dump_default=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        ordered = True

class SkillCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    category = fields.String(validate=validate.Length(max=50))
    description = fields.String(validate=validate.Length(max=255))
    is_hot = fields.Boolean(dump_default=False)

class SkillUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=1, max=50))
    category = fields.String(validate=validate.Length(max=50))
    description = fields.String(validate=validate.Length(max=255))
    is_hot = fields.Boolean()


# --- Freelancer Skill Association Schema ---
class FreelancerSkillSchema(ma.Schema):
    # user_id is implicit in the context (e.g., /users/me/skills)
    skill_id = fields.Integer(required=True)
    proficiency_level = fields.String(validate=validate.OneOf([e.value for e in ProficiencyLevelEnum]))
    years_of_experience = fields.Integer(validate=validate.Range(min=0, max=50))
    certificate_url = fields.URL(validate=validate.Length(max=512))
    # certificate_verified: Should be dump_only, set by admin/system
    certificate_verified = fields.Boolean(dump_only=True, dump_default=False)

    # Nested skill details for output
    skill = fields.Nested(SkillSchema, dump_only=True) # Show skill details when listing freelancer skills

    class Meta:
        ordered = True

class FreelancerSkillCreateSchema(ma.Schema):
    skill_id = fields.Integer(required=True)
    proficiency_level = fields.String(validate=validate.OneOf([e.value for e in ProficiencyLevelEnum]))
    years_of_experience = fields.Integer(validate=validate.Range(min=0, max=50))
    certificate_url = fields.URL(validate=validate.Length(max=512))

class FreelancerSkillUpdateSchema(ma.Schema):
    proficiency_level = fields.String(validate=validate.OneOf([e.value for e in ProficiencyLevelEnum]))
    years_of_experience = fields.Integer(validate=validate.Range(min=0, max=50))
    certificate_url = fields.URL(validate=validate.Length(max=512))
