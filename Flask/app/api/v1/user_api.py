from flask_restx import Namespace, Resource, fields
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.user_service import user_service
from ...schemas.user_schema import UserSchema, UserPublicSchema # For serializing user output and potentially validating updates
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthenticationException
from ...utils.helpers import api_success_response, api_error_response
# Assuming user_public_output_model is defined in auth_api or a shared models file
# For now, let's redefine a similar one or import if it was made sharable.
from .auth_api import user_public_output_model # Re-use from auth_api for consistency

ns = Namespace('users', description='用户相关操作 (需要认证)')

# Model for updating user details (subset of fields)
user_update_input_model = ns.model('UserUpdateInput', {
    'email': fields.String(description='新邮箱地址'),
    # 'nickname': fields.String(description='新昵称'), # Nickname is in profile table, not user table
    # Other fields from User model that can be updated by the user themselves
})

password_change_input_model = ns.model('PasswordChangeInput', {
    'old_password': fields.String(required=True, description='当前密码'),
    'new_password': fields.String(required=True, description='新密码', min_length=6)
})

user_role_update_input = ns.model('UserRoleUpdateInput', {
    'current_role': fields.String(required=True, description='当前角色')
})

@ns.route('/me')
class UserSelfResource(Resource):
    @jwt_required()
    @ns.response(200, '成功获取当前用户信息', model=user_public_output_model)
    def get(self):
        """获取当前登录用户的信息"""
        user_id = get_jwt_identity()
        
        try:
            user = user_service.get_user_by_id(user_id)
            return user_service.user_to_dict(user), 200
        except NotFoundException as e:
            return {"code": 40401, "message": str(e), "data": None}, 404
        except Exception as e:
            current_app.logger.error(f"获取用户信息失败: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

    @jwt_required()
    @ns.expect(user_update_input_model)
    @ns.response(200, '用户信息更新成功', model=user_public_output_model)
    def put(self):
        """更新当前登录用户的基本信息"""
        user_id = get_jwt_identity()
        data = request.json
        
        try:
            user = user_service.update_user(user_id, data)
            return user_service.user_to_dict(user), 200
        except NotFoundException as e:
            return {"code": 40401, "message": str(e), "data": None}, 404
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"更新用户信息失败: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

@ns.route('/me/change-password')
class UserChangePasswordResource(Resource):
    @jwt_required()
    @ns.expect(password_change_input_model)
    @ns.response(200, '密码修改成功')
    def post(self):
        """修改当前登录用户的密码"""
        user_id = get_jwt_identity()
        data = request.json
        
        try:
            user_service.change_password(user_id, data.get('old_password'), data.get('new_password'))
            return {"code": 0, "message": "密码修改成功", "data": None}, 200
        except NotFoundException as e:
            return {"code": 40401, "message": str(e), "data": None}, 404
        except AuthenticationException as e:
            return {"code": 40101, "message": str(e), "data": None}, 401
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"修改密码失败: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

@ns.route('/me/role')
class UserCurrentRoleResource(Resource):
    @jwt_required()
    @ns.expect(user_role_update_input)
    @ns.response(200, '角色切换成功', model=user_public_output_model)
    def put(self):
        """切换当前登录用户的角色"""
        user_id = get_jwt_identity()
        data = request.json
        
        try:
            user = user_service.switch_role(user_id, data.get('current_role'))
            return user_service.user_to_dict(user), 200
        except NotFoundException as e:
            return {"code": 40401, "message": str(e), "data": None}, 404
        except BusinessException as e:
            return {"code": e.code, "message": str(e), "data": None}, 400
        except Exception as e:
            current_app.logger.error(f"切换角色失败: {str(e)}")
            return {"code": 50001, "message": "服务器内部发生未知错误。", "data": None}, 500

@ns.route('/<string:user_uuid>')
@ns.param('user_uuid', '用户的UUID')
class UserPublicProfileResource(Resource):
    @ns.doc(description="1.4. 获取用户公开信息 (User - Public)")
    def get(self, user_uuid):
        """获取用户公开信息"""
        try:
            # 调用服务方法获取用户公开信息
            user = user_service.get_public_user_profile_by_uuid(user_uuid)
            
            # 使用UserPublicSchema序列化，只返回公开字段
            user_data = UserPublicSchema().dump(user)
            
            return api_success_response(user_data)
        except NotFoundException as e:
            raise e
        except Exception as e:
            current_app.logger.error(f"获取用户公开信息失败: {str(e)}")
            raise BusinessException(message="获取用户公开信息失败", internal_message=str(e))