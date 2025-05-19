from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # 用于生成 JWT

from app.services.user_service import user_service # 导入 UserService 实例
from app.schemas.user_schema import UserSchema # For serializing user output
from app.utils.exceptions import AuthenticationException, InvalidUsageException, BusinessException # For catching
from app.utils.helpers import api_success_response, api_error_response # 假设有响应格式化帮助函数

# 创建 Namespace
ns = Namespace('auth', description='用户认证操作')

# 定义 API模型的输入输出，用于 Swagger 文档和数据校验
# 注册模型
user_registration_input_model = ns.model('UserRegistrationInput', {
    'phone_number': fields.String(required=True, description='手机号', example='13800138000'),
    'password': fields.String(required=True, description='密码', example='password123'),
    'user_type': fields.String(description='用户类型 (freelancer/employer), 默认为 freelancer', example='freelancer', enum=['freelancer', 'employer'])
})

# 登录模型
user_login_input_model = ns.model('UserLoginInput', {
    'phone_number': fields.String(required=True, description='手机号', example='13800138000'),
    'password': fields.String(required=True, description='密码', example='password123'),
})

# 用户信息输出模型 (不含密码)
user_public_output_model = ns.model('UserPublicOutput', {
    'id': fields.Integer(readonly=True, description='用户唯一ID'),
    'uuid': fields.String(readonly=True, description='用户唯一UUID'), # 添加UUID
    'phone_number': fields.String(readonly=True, description='手机号'),
    'email': fields.String(readonly=True, description='邮箱'),
    'nickname': fields.String(readonly=True, description='昵称'), # 添加昵称
    'current_role': fields.String(readonly=True, description='用户当前活跃角色', enum=['freelancer', 'employer']),
    'available_roles': fields.List(fields.String, readonly=True, description='用户拥有的角色列表'),
    'status': fields.String(readonly=True, description='账号状态'),
    'last_login_at': fields.DateTime(readonly=True, description='最后登录时间'),
    'registered_at': fields.DateTime(readonly=True, description='注册时间'),
})

# 登录成功响应模型
login_success_output_model = ns.model('LoginSuccessOutput', {
    'access_token': fields.String(readonly=True, description='JWT访问令牌'),
    'user': fields.Nested(user_public_output_model, description='用户信息')
})

@ns.route('/register')
class UserRegistration(Resource):
    @ns.expect(user_registration_input_model)
    @ns.response(201, 'User registered successfully', model=user_public_output_model)
    @ns.response(400, 'Invalid input')
    @ns.response(409, 'User already exists')
    def post(self):
        """用户注册"""
        data = request.json
        try:
            # 调用 service 层进行注册
            user = user_service.register_user(data)
            # 序列化用户信息以返回
            user_schema = UserSchema()
            return api_success_response(user_schema.dump(user), 201)
        except (InvalidUsageException, BusinessException) as e:
            return api_error_response(str(e), e.status_code if hasattr(e, 'status_code') else 400)
        except Exception as e:
            # Log the exception e
            return api_error_response("注册失败，请稍后再试", 500)

@ns.route('/login')
class UserLogin(Resource):
    @ns.expect(user_login_input_model)
    @ns.response(200, 'Login successful', model=login_success_output_model)
    @ns.response(400, 'Invalid input')
    @ns.response(401, 'Authentication failed')
    def post(self):
        """用户登录"""
        data = request.json
        phone_number = data.get('phone_number')
        password = data.get('password')

        try:
            user, token = user_service.login_user(phone_number, password)
            user_schema = UserSchema()
            user_data = user_schema.dump(user)
            
            # 确保 available_roles 存在且是列表
            if 'available_roles' not in user_data or not isinstance(user_data['available_roles'], list):
                user_data['available_roles'] = [user.current_role] if user.current_role else []
            
            return api_success_response({
                'access_token': token,
                'user': user_data
            })
        except AuthenticationException as e:
            return api_error_response(str(e), 401)
        except InvalidUsageException as e:
            return api_error_response(str(e), 400)
        except BusinessException as e:
            return api_error_response(str(e), e.status_code if hasattr(e, 'status_code') else 500)
        except Exception as e:
            # Log the exception e
            return api_error_response("登录失败，请稍后再试", 500)

# 可以添加一个获取当前用户信息的接口，用于验证token和获取用户信息
@ns.route('/me')
class UserMe(Resource):
    @jwt_required()
    @ns.response(200, 'User profile retrieved successfully', model=user_public_output_model)
    @ns.response(401, 'Unauthorized')
    @ns.response(404, 'User not found')
    def get(self):
        """获取当前登录用户信息"""
        current_user_identity = get_jwt_identity() # This will be user's uuid or id
        try:
            # Assuming get_jwt_identity() returns the user's primary key (id or uuid)
            # Adjust based on what you store in the JWT (e.g., user.id or user.uuid)
            # If it's UUID, you might need a get_user_by_uuid method in your service
            user = user_service.get_user_by_uuid(current_user_identity) # Or get_user_by_id if ID is used
            if not user:
                 user = user_service.get_user_by_id(current_user_identity)
            
            if not user:
                return api_error_response("用户未找到", 404)

            user_schema = UserSchema()
            user_data = user_schema.dump(user)
            # Ensure available_roles is present and is a list
            if 'available_roles' not in user_data or not isinstance(user_data['available_roles'], list):
                user_data['available_roles'] = [user.current_role] if user.current_role else []

            return api_success_response(user_data)
        except Exception as e:
            # Log the exception e
            return api_error_response(f"获取用户信息失败: {str(e)}", 500)