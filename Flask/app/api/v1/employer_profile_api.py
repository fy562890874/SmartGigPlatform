from flask_restx import Namespace, Resource, fields
from flask import request, current_app
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
        """获取当前登录雇主的档案信息"""
        user_id = get_jwt_identity()
        
        try:
            profile = employer_profile_service.get_profile_by_user_id(user_id)
            return profile, 200
        except NotFoundException as e:
            return {"code": 40401, "message": str(e), "data": None}, 404
        except Exception as e:
            current_app.logger.error(f"Error retrieving employer profile: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

    @jwt_required()
    @ns.expect(employer_profile_input_model, validate=True)
    @ns.response(200, '雇主档案更新成功', model=employer_profile_model)
    @ns.response(201, '雇主档案创建成功', model=employer_profile_model)
    def put(self):
        """创建或更新当前雇主档案"""
        user_id = get_jwt_identity()
        data = request.json
        
        # 确保传入了必需字段
        if 'profile_type' not in data:
            return {"code": 40001, "message": "缺少必需字段 'profile_type'", "data": None}, 400
        
        try:
            # 检查是否已有档案
            try:
                profile = employer_profile_service.get_profile_by_user_id(user_id)
                # 更新现有档案
                updated_profile = employer_profile_service.update_profile(user_id, data)
                return updated_profile, 200
            except NotFoundException:
                # 创建新档案
                new_profile = employer_profile_service.create_profile(user_id, data)
                return new_profile, 201
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"Error updating employer profile: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

@ns.route('/me/avatar')
class EmployerProfileAvatarResource(Resource):
    @jwt_required()
    @ns.response(200, '头像上传成功')
    def post(self):
        """上传雇主头像"""
        user_id = get_jwt_identity()
        
        if 'avatar' not in request.files:
            return {"code": 40001, "message": "没有上传图片文件", "data": None}, 400
            
        avatar_file = request.files['avatar']
        
        if avatar_file.filename == '':
            return {"code": 40001, "message": "未选择文件", "data": None}, 400
            
        try:
            avatar_url = employer_profile_service.upload_avatar(user_id, avatar_file)
            return {"code": 0, "message": "头像上传成功", "data": {"avatar_url": avatar_url}}, 200
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"Error uploading avatar: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

@ns.route('/me/license')
class EmployerProfileLicenseResource(Resource):
    @jwt_required()
    @ns.response(200, '营业执照上传成功')
    def post(self):
        """上传雇主营业执照"""
        user_id = get_jwt_identity()
        
        if 'license' not in request.files:
            return {"code": 40001, "message": "没有上传执照文件", "data": None}, 400
            
        license_file = request.files['license']
        
        if license_file.filename == '':
            return {"code": 40001, "message": "未选择文件", "data": None}, 400
            
        try:
            license_url = employer_profile_service.upload_license(user_id, license_file)
            return {"code": 0, "message": "营业执照上传成功", "data": {"business_license_photo_url": license_url}}, 200
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"Error uploading license: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500 