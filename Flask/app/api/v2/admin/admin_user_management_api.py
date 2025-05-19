# app/apis/v2/admin_user_management_api.py
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
# Import services, schemas, exceptions, helpers

ns = Namespace('admin_users_v2', description='[Admin] 用户管理') # Ensure unique ns name

# Placeholder: Define models
admin_user_list_item_model = ns.model('AdminUserListItemV2', { # Example
    'uuid': fields.String(),
    'phone_number': fields.String(),
    'current_role': fields.String(),
    'status': fields.String(),
    'registered_at': fields.DateTime()
})
paginated_admin_users_model = ns.model('PaginatedAdminUsersV2', {
    'items': fields.List(fields.Nested(admin_user_list_item_model)),
    # ... pagination fields
})
user_status_update_input_model = ns.model('UserStatusUpdateInputV2', {
    'status': fields.String(required=True, enum=['active', 'inactive', 'banned']),
    'ban_reason': fields.String()
})

@ns.route('') # Mapped to /admin/users
class AdminUserListResource(Resource):
    @jwt_required() # + Admin role check
    @ns.response(200, 'Success', model=paginated_admin_users_model)
    @ns.doc(description="12.1. 管理用户列表 (Admin)")
    def get(self):
        return {"message": "API 12.1 GET /admin/users - Placeholder"}, 200

@ns.route('/<string:user_uuid>/status')
@ns.param('user_uuid', '用户UUID')
class AdminUserStatusResource(Resource):
    @jwt_required() # + Admin role check
    @ns.expect(user_status_update_input_model)
    @ns.response(200, 'Success', model=admin_user_list_item_model) # Responding with updated user
    @ns.doc(description="12.2. 更新用户状态 (Admin)")
    def put(self, user_uuid):
        return {"message": f"API 12.2 PUT /admin/users/{user_uuid}/status - Placeholder"}, 200