"""Job and Job Application Schemas"""
from ..core.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from ..models.job import SalaryTypeEnum, JobStatusEnum, JobApplicationStatusEnum
from .user_schema import UserSchema # Assuming user_schema exists for employer details
from .skill_schema import SkillSchema # Assuming skill_schema exists

# --- Basic Schemas for Nesting ---
class UserBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nickname = fields.String(dump_only=True)
    avatar_url = fields.URL(dump_only=True)

class JobBasicSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)
    status = fields.String(dump_only=True)

# --- Skill Requirement Schema ---
class JobRequiredSkillSchema(ma.Schema):
    skill_id = fields.Integer(required=True)
    is_mandatory = fields.Boolean(dump_default=True)
    # Optionally nest Skill details
    skill = fields.Nested(SkillSchema, dump_only=True)

    class Meta:
        ordered = True

# --- Job Schemas ---
class JobSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    employer_user_id = fields.Integer(dump_only=True) # Set from JWT on creation
    title = fields.String(required=True, validate=validate.Length(min=5, max=100))
    description = fields.String(required=True, validate=validate.Length(min=20))
    job_category = fields.String(required=True, validate=validate.Length(max=50))
    job_tags = fields.List(fields.String(validate=validate.Length(max=30))) # List of strings

    location_address = fields.String(required=True, validate=validate.Length(max=200))
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    # location_point: How to handle Point? Maybe Tuple or Dict?
    # For input, maybe expect {'latitude': float, 'longitude': float}
    # For output, maybe {'latitude': float, 'longitude': float} or WKT string
    location_point = fields.Method("serialize_point", "deserialize_point", description="Geo coordinates (latitude, longitude)")

    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    duration_estimate = fields.Decimal(places=2, as_string=True, validate=validate.Range(min=0))

    salary_amount = fields.Decimal(places=2, as_string=True, required=True, validate=validate.Range(min=0))
    salary_type = fields.String(required=True, validate=validate.OneOf([e.value for e in SalaryTypeEnum]))
    salary_negotiable = fields.Boolean(dump_default=False)

    required_people = fields.Integer(required=True, validate=validate.Range(min=1), dump_default=1)
    accepted_people = fields.Integer(dump_only=True, dump_default=0)

    skill_requirements = fields.String() # Text description
    # required_skills_assoc: Nested list for specific skills
    required_skills = fields.Nested(JobRequiredSkillSchema, many=True, data_key="required_skills_assoc")

    is_urgent = fields.Boolean(dump_default=False)
    status = fields.String(validate=validate.OneOf([e.value for e in JobStatusEnum]), dump_only=True, dump_default=JobStatusEnum.pending_review.value)
    cancellation_reason = fields.String(dump_only=True) # Set via specific action/endpoint
    view_count = fields.Integer(dump_only=True, dump_default=0)
    application_deadline = fields.DateTime(allow_none=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    employer = fields.Nested(UserBasicSchema, dump_only=True) # Simplified employer info

    class Meta:
        ordered = True

    def serialize_point(self, obj):
        # 将数据库中的GeoJSON Point对象转换为API输出格式
        if hasattr(obj, 'location_point') and obj.location_point is not None:
            # 如果location_point是GeoJSON格式(字典)
            if isinstance(obj.location_point, dict):
                if 'type' in obj.location_point and obj.location_point['type'] == 'Point' and 'coordinates' in obj.location_point:
                    # 标准GeoJSON格式，直接返回
                    return obj.location_point
            # 如果是字符串(可能是WKT或JSON字符串)
            elif isinstance(obj.location_point, str):
                try:
                    # 尝试解析为JSON
                    import json
                    geo_json = json.loads(obj.location_point)
                    if isinstance(geo_json, dict) and 'type' in geo_json and 'coordinates' in geo_json:
                        return geo_json
                except json.JSONDecodeError:
                    # 可能是WKT格式，尝试解析
                    pass
            # 其他情况，返回字符串表示
            return str(obj.location_point)
        return None

    def deserialize_point(self, value):
        # 将API输入的地理位置转换为数据库存储格式
        if value is None:
            return None
            
        # 如果已经是GeoJSON格式
        if isinstance(value, dict) and 'type' in value and value['type'] == 'Point' and 'coordinates' in value:
            # 检查坐标的有效性
            try:
                longitude, latitude = value['coordinates']
                if isinstance(longitude, (int, float)) and isinstance(latitude, (int, float)):
                    return value  # 直接返回有效的GeoJSON
            except (ValueError, TypeError):
                raise ValidationError("GeoJSON坐标格式无效。应为[经度, 纬度]。")
        
        # 如果提供的是经纬度键值对
        if isinstance(value, dict) and 'latitude' in value and 'longitude' in value:
            try:
                lat = float(value['latitude'])
                lon = float(value['longitude'])
                if -90 <= lat <= 90 and -180 <= lon <= 180:  # 检查坐标范围有效性
                    return {"type": "Point", "coordinates": [lon, lat]}
                else:
                    raise ValidationError("经纬度超出有效范围。纬度:-90到90，经度:-180到180。")
            except (ValueError, TypeError):
                raise ValidationError("无效的经纬度格式。应为数值。")
                
        # 不支持的格式
        raise ValidationError("无效的地理位置格式。支持的格式为GeoJSON Point或{latitude:纬度, longitude:经度}。")

    @validates_schema
    def validate_times(self, data, **kwargs):
        if 'start_time' in data and 'end_time' in data and data['start_time'] >= data['end_time']:
            raise ValidationError("End time must be after start time.", "end_time")
        if 'application_deadline' in data and data['application_deadline'] is not None:
            if 'start_time' in data and data['application_deadline'] >= data['start_time']:
                 raise ValidationError("Application deadline must be before the job start time.", "application_deadline")
            if data['application_deadline'] <= fields.DateTime()._deserialize(None, None, None): # Compare with now
                 raise ValidationError("Application deadline must be in the future.", "application_deadline")


class JobCreateSchema(JobSchema):
     # Inherits most fields, override or add as needed
     # Status is usually set by the system, so exclude from direct creation input
     class Meta:
        exclude = ("id", "employer_user_id", "accepted_people", "status", "cancellation_reason", "view_count", "created_at", "updated_at", "employer")
        ordered = True


class JobUpdateSchema(ma.Schema):
    # Allow updating specific fields
    title = fields.String(validate=validate.Length(min=5, max=100))
    description = fields.String(validate=validate.Length(min=20))
    job_category = fields.String(validate=validate.Length(max=50))
    job_tags = fields.List(fields.String(validate=validate.Length(max=30)))
    location_address = fields.String(validate=validate.Length(max=200))
    location_province = fields.String(validate=validate.Length(max=50))
    location_city = fields.String(validate=validate.Length(max=50))
    location_district = fields.String(validate=validate.Length(max=50))
    location_point = fields.Method("serialize_point", "deserialize_point", description="Geo coordinates (latitude, longitude)") # Re-declare method if needed in subclass
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    duration_estimate = fields.Decimal(places=2, as_string=True, validate=validate.Range(min=0))
    salary_amount = fields.Decimal(places=2, as_string=True, validate=validate.Range(min=0))
    salary_type = fields.String(validate=validate.OneOf([e.value for e in SalaryTypeEnum]))
    salary_negotiable = fields.Boolean()
    required_people = fields.Integer(validate=validate.Range(min=1))
    skill_requirements = fields.String()
    required_skills = fields.Nested(JobRequiredSkillSchema, many=True, data_key="required_skills_assoc")
    is_urgent = fields.Boolean()
    application_deadline = fields.DateTime(allow_none=True)

    # 与JobSchema保持一致
    def serialize_point(self, obj):
        # 将数据库中的GeoJSON Point对象转换为API输出格式
        if hasattr(obj, 'location_point') and obj.location_point is not None:
            # 如果location_point是GeoJSON格式(字典)
            if isinstance(obj.location_point, dict):
                if 'type' in obj.location_point and obj.location_point['type'] == 'Point' and 'coordinates' in obj.location_point:
                    # 标准GeoJSON格式，直接返回
                    return obj.location_point
            # 如果是字符串(可能是WKT或JSON字符串)
            elif isinstance(obj.location_point, str):
                try:
                    # 尝试解析为JSON
                    import json
                    geo_json = json.loads(obj.location_point)
                    if isinstance(geo_json, dict) and 'type' in geo_json and 'coordinates' in geo_json:
                        return geo_json
                except json.JSONDecodeError:
                    # 可能是WKT格式，尝试解析
                    pass
            # 其他情况，返回字符串表示
            return str(obj.location_point)
        return None

    def deserialize_point(self, value):
        # 将API输入的地理位置转换为数据库存储格式
        if value is None:
            return None
            
        # 如果已经是GeoJSON格式
        if isinstance(value, dict) and 'type' in value and value['type'] == 'Point' and 'coordinates' in value:
            # 检查坐标的有效性
            try:
                longitude, latitude = value['coordinates']
                if isinstance(longitude, (int, float)) and isinstance(latitude, (int, float)):
                    return value  # 直接返回有效的GeoJSON
            except (ValueError, TypeError):
                raise ValidationError("GeoJSON坐标格式无效。应为[经度, 纬度]。")
        
        # 如果提供的是经纬度键值对
        if isinstance(value, dict) and 'latitude' in value and 'longitude' in value:
            try:
                lat = float(value['latitude'])
                lon = float(value['longitude'])
                if -90 <= lat <= 90 and -180 <= lon <= 180:  # 检查坐标范围有效性
                    return {"type": "Point", "coordinates": [lon, lat]}
                else:
                    raise ValidationError("经纬度超出有效范围。纬度:-90到90，经度:-180到180。")
            except (ValueError, TypeError):
                raise ValidationError("无效的经纬度格式。应为数值。")
                
        # 不支持的格式
        raise ValidationError("无效的地理位置格式。支持的格式为GeoJSON Point或{latitude:纬度, longitude:经度}。")

    @validates_schema
    def validate_times_on_update(self, data, **kwargs):
        # Need to handle partial updates - compare with existing object if possible
        # This validation might be better handled in the service layer for updates
        start = data.get('start_time')
        end = data.get('end_time')
        deadline = data.get('application_deadline')

        if start and end and start >= end:
             raise ValidationError("End time must be after start time.", "end_time")
        if deadline is not None:
            # Comparing deadline with start time requires knowing the *final* start time (potentially existing one)
            # Comparing deadline with now is still valid
             if deadline <= fields.DateTime()._deserialize(None, None, None):
                 raise ValidationError("Application deadline must be in the future.", "application_deadline")
        # Add more complex validation logic here or in service layer


# --- Job Application Schemas ---
class JobApplicationSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    job_id = fields.Integer(required=True) # Required for creation context
    freelancer_user_id = fields.Integer(dump_only=True) # Set from JWT
    employer_user_id = fields.Integer(dump_only=True) # Derived from job
    apply_message = fields.String(validate=validate.Length(max=1000))
    status = fields.String(validate=validate.OneOf([e.value for e in JobApplicationStatusEnum]), dump_only=True, dump_default=JobApplicationStatusEnum.pending.value)
    applied_at = fields.DateTime(dump_only=True)
    processed_at = fields.DateTime(dump_only=True)
    rejection_reason = fields.String(dump_only=True) # Set via specific action
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Relationships (dump only)
    job = fields.Nested(JobBasicSchema, dump_only=True)
    freelancer = fields.Nested(UserBasicSchema, dump_only=True, attribute="freelancer_user")
    employer = fields.Nested(UserBasicSchema, dump_only=True, attribute="employer_user") # Redundant but maybe useful

    class Meta:
        ordered = True

class JobApplicationCreateSchema(ma.Schema):
    job_id = fields.Integer(required=True)
    apply_message = fields.String(validate=validate.Length(max=1000))

class JobApplicationUpdateSchema(ma.Schema): # For Employer actions
    status = fields.String(required=True, validate=validate.OneOf([
        JobApplicationStatusEnum.accepted.value,
        JobApplicationStatusEnum.rejected.value
    ]))
    rejection_reason = fields.String(validate=validate.Length(max=500))

    @validates_schema
    def validate_rejection_reason(self, data, **kwargs):
        if data.get('status') == JobApplicationStatusEnum.rejected.value and not data.get('rejection_reason'):
            # Depending on requirements, reason might be optional or mandatory for rejection
            # raise ValidationError("Rejection reason is required when rejecting an application.", "rejection_reason")
            pass
        if data.get('status') == JobApplicationStatusEnum.accepted.value and data.get('rejection_reason'):
             raise ValidationError("Rejection reason should not be provided when accepting an application.", "rejection_reason")

class JobApplicationCancelSchema(ma.Schema): # For Freelancer action
    # No input needed, just the action on the specific application ID
    pass
