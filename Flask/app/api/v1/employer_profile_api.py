from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.employer_profile_service import employer_profile_service
from ...schemas.profile_schema import EmployerProfileSchema # For serialization & input validation
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthorizationException
from ...utils.helpers import api_success_response
from ...models.profile import EmployerProfile # Import the model for querying

ns = Namespace('profiles/employer', description='雇主用户档案操作 (需要认证)')

# API Model for EmployerProfile (align with EmployerProfileSchema)
employer_profile_model = ns.model('EmployerProfileOutput', {
    'user_id': fields.Integer(readonly=True, description='关联的用户ID'),
    'profile_type': fields.String(description='档案类型 (individual/company)', enum=['individual', 'company']),
    'real_name': fields.String(description='真实姓名 (个人或法人/联系人)'),
    'avatar_url': fields.String(description='头像/Logo URL'),
    'nickname': fields.String(description='昵称/简称'),
    'location_province': fields.String(description='所在省份'),
    'location_city': fields.String(description='所在城市'),
    'location_district': fields.String(description='所在区县'),
    'contact_phone': fields.String(description='联系电话'),
    'verification_status': fields.String(readonly=True, description='认证状态'),
    'credit_score': fields.Integer(readonly=True, description='信用分'),
    'average_rating': fields.Float(readonly=True, description='平均评分'),
    'total_jobs_posted': fields.Integer(readonly=True, description='累计发布工作数'),
    # Company specific fields
    'company_name': fields.String(description='公司名称 (企业认证后填写)'),
    'business_license_number': fields.String(description='统一社会信用代码/营业执照号'),
    'business_license_photo_url': fields.String(description='营业执照照片 URL'),
    'company_address': fields.String(description='公司地址'),
    'company_description': fields.String(description='公司简介'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

# Input model for creation/update
employer_profile_input_model = ns.model('EmployerProfileInput', {
    'profile_type': fields.String(required=True, description='档案类型', enum=['individual', 'company']),
    'real_name': fields.String(description='真实姓名'),
    'avatar_url': fields.String(description='头像/Logo URL'),
    'nickname': fields.String(description='昵称/简称'),
    'location_province': fields.String(description='所在省份'),
    'location_city': fields.String(description='所在城市'),
    'location_district': fields.String(description='所在区县'),
    'contact_phone': fields.String(description='联系电话'),
    # Company specific fields
    'company_name': fields.String(description='公司名称'),
    'business_license_number': fields.String(description='统一社会信用代码'),
    'business_license_photo_url': fields.String(description='营业执照照片 URL'),
    'company_address': fields.String(description='公司地址'),
    'company_description': fields.String(description='公司简介')
})

@ns.route('/me') # Endpoint for the current authenticated user's employer profile
class EmployerProfileSelfResource(Resource):
    @jwt_required()
    @ns.response(200, '获取雇主档案成功', model=employer_profile_model)
    def get(self):
        """获取当前登录用户的雇主档案"""
        current_user_id = get_jwt_identity()
        try:
            profile = employer_profile_service.get_profile_by_user_id(current_user_id)
            profile_data = EmployerProfileSchema().dump(profile)
            return api_success_response(profile_data)
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message="获取雇主档案时发生意外错误。", status_code=500, error_code=50001)

    @jwt_required()
    @ns.expect(employer_profile_input_model, validate=True)
    @ns.response(200, '雇主档案更新成功', model=employer_profile_model)
    @ns.response(201, '雇主档案创建成功', model=employer_profile_model)
    def put(self):
        """创建或更新当前登录用户的雇主档案"""
        current_user_id = get_jwt_identity()
        data = request.json
        # schema = EmployerProfileSchema(partial=True) # Use for validation
        try:
            # validated_data = schema.load(data)
            profile_exists = EmployerProfile.query.filter_by(user_id=current_user_id).first() is not None
            profile = employer_profile_service.create_or_update_profile(current_user_id, data, is_creation=not profile_exists)
            profile_data = EmployerProfileSchema().dump(profile)
            status_code = 200 if profile_exists else 201
            return api_success_response(profile_data, status_code)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            action = "更新" if profile_exists else "创建"
            raise BusinessException(message=f"{action}雇主档案时发生意外错误: {str(e)}", status_code=500, error_code=50001) 