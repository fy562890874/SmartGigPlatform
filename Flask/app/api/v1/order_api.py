from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from ...services.order_service import order_service
from ...schemas.order_schema import OrderSchema, OrderActionSchema, OrderTimeUpdateSchema
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthorizationException
from ...utils.helpers import api_success_response
from ...models.user import User # To get current_user role

ns = Namespace('orders', description='订单管理')

# --- API Models (based on OrderSchema and related action schemas) ---
order_output_model = ns.model('OrderOutput', {
    'id': fields.Integer(readonly=True, description='订单ID'),
    'job_id': fields.Integer(readonly=True, description='工作ID'),
    'application_id': fields.Integer(readonly=True, description='申请ID'),
    'freelancer_user_id': fields.Integer(readonly=True, description='零工用户ID'),
    'employer_user_id': fields.Integer(readonly=True, description='雇主用户ID'),
    'order_amount': fields.Float(description='订单金额 (元)'),
    'platform_fee': fields.Float(description='平台服务费 (元)'),
    'freelancer_income': fields.Float(description='零工实际收入 (元)'),
    'start_time_scheduled': fields.DateTime(description='计划开始时间'),
    'end_time_scheduled': fields.DateTime(description='计划结束时间'),
    'start_time_actual': fields.DateTime(description='实际开始时间'),
    'end_time_actual': fields.DateTime(description='实际结束时间'),
    'work_duration_actual': fields.Float(description='实际工时(小时)'),
    'status': fields.String(readonly=True, description='订单状态'),
    'freelancer_confirmation_status': fields.String(readonly=True, description='零工确认状态'),
    'employer_confirmation_status': fields.String(readonly=True, description='雇主确认状态'),
    'confirmation_deadline': fields.DateTime(description='确认截止时间'),
    'cancellation_reason': fields.String(description='取消原因'),
    'cancelled_by': fields.String(description='取消方'),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'updated_at': fields.DateTime(readonly=True, description='更新时间'),
    # Simplified nested objects for brevity in API model, full details via schemas
    'job': fields.Nested(ns.model('JobBasicForOrder', {
        'id': fields.Integer(), 'title': fields.String()
    })), 
    'freelancer': fields.Nested(ns.model('UserBasicForOrderFreelancer', {
        'id': fields.Integer(), 'nickname': fields.String(), 'avatar_url': fields.String()
    })), 
    'employer': fields.Nested(ns.model('UserBasicForOrderEmployer', {
        'id': fields.Integer(), 'nickname': fields.String(), 'avatar_url': fields.String()
    }))
})

paginated_order_model = ns.model('PaginatedOrderResponse', {
    'items': fields.List(fields.Nested(order_output_model)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_pages': fields.Integer(description='总页数'),
    'total_items': fields.Integer(description='总条目数')
})

order_action_input_model = ns.model('OrderActionInput', {
    'action': fields.String(required=True, description='执行的操作', 
                           enum=['start_work', 'complete_work', 'confirm_completion', 'cancel_order']),
    'cancellation_reason': fields.String(description='取消原因 (当 action 为 cancel_order 时可能需要)'),
    'start_time_actual': fields.DateTime(description='实际开始时间 (当 action 为 complete_work 时可选)'),
    'end_time_actual': fields.DateTime(description='实际结束时间 (当 action 为 complete_work 时可选)')
})

order_time_update_input_model = ns.model('OrderTimeUpdateInput', {
    'start_time_actual': fields.DateTime(required=True, description='实际开始时间 (ISO 8601)'),
    'end_time_actual': fields.DateTime(required=True, description='实际结束时间 (ISO 8601)')
})

# --- Parsers ---
order_list_parser = reqparse.RequestParser()
order_list_parser.add_argument('page', type=int, location='args', default=1, help='页码')
order_list_parser.add_argument('per_page', type=int, location='args', default=10, help='每页数量')
order_list_parser.add_argument('status', type=str, location='args', help='筛选订单状态')
order_list_parser.add_argument('role', type=str, location='args', choices=('freelancer', 'employer'), help='用户角色 (freelancer/employer) - 若不提供, 会尝试从JWT用户当前角色推断')
# Add sort_by later if needed


# --- Routes ---
@ns.route('/')
class OrderListResource(Resource):
    @jwt_required()
    @ns.expect(order_list_parser)
    @ns.response(200, '获取订单列表成功', model=paginated_order_model)
    def get(self):
        """用户获取自己的订单列表 (根据角色区分是零工还是雇主)"""
        user_id = get_jwt_identity()
        args = order_list_parser.parse_args()
        
        # Determine user_role: from argument, or from JWT current_user.current_role
        user_role_arg = args.get('role')
        # Assuming current_user is the User object from flask_jwt_extended. It has `current_role`
        # This requires current_user loader to be configured to return the User object.
        # If get_jwt_identity() only returns user_id, we need to fetch the user object.
        jwt_user = User.query.get(user_id) # Fetch user to get current_role if not directly available
        if not jwt_user:
            raise NotFoundException("用户不存在。")
        
        user_role_to_use = user_role_arg if user_role_arg else jwt_user.current_role
        if not user_role_to_use:
            raise InvalidUsageException("无法确定用户角色。请提供 'role' 参数或确保用户已设置当前角色。")

        filters = {'status': args.get('status')}
        filters = {k: v for k, v in filters.items() if v is not None}

        try:
            paginated_orders = order_service.get_orders_for_user(
                user_id=user_id,
                user_role=user_role_to_use,
                filters=filters,
                page=args.get('page'),
                per_page=args.get('per_page')
            )
            order_data = OrderSchema(many=True).dump(paginated_orders.items)
            return api_success_response({
                'items': order_data,
                'page': paginated_orders.page,
                'per_page': paginated_orders.per_page,
                'total_pages': paginated_orders.pages,
                'total_items': paginated_orders.total
            })
        except (AuthorizationException, InvalidUsageException, BusinessException) as e:
            raise e
        except Exception as e:
            # Log e
            raise BusinessException(message=f"获取订单列表失败: {str(e)}", status_code=500)

@ns.route('/<int:order_id>')
@ns.param('order_id', '订单ID')
class OrderDetailResource(Resource):
    @jwt_required()
    @ns.response(200, '获取订单详情成功', model=order_output_model)
    @ns.response(403, '无权访问此订单')
    @ns.response(404, '订单未找到')
    def get(self, order_id):
        """获取指定订单详情 (仅限订单参与方)"""
        user_id = get_jwt_identity()
        try:
            order = order_service.get_order_by_id(order_id, user_id)
            order_data = OrderSchema().dump(order)
            return api_success_response(order_data)
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            # Log e
            raise BusinessException(message=f"获取订单详情失败: {str(e)}", status_code=500)

@ns.route('/<int:order_id>/actions')
@ns.param('order_id', '订单ID')
class OrderActionResource(Resource):
    @jwt_required()
    @ns.expect(order_action_input_model)
    @ns.response(200, '订单操作成功', model=order_output_model)
    @ns.response(400, '无效操作或请求参数错误')
    @ns.response(403, '无权执行此操作')
    @ns.response(404, '订单未找到')
    @ns.response(409, '操作与当前订单状态冲突') # Business rule violation
    def post(self, order_id):
        """执行订单操作 (开始工作、完成工作、确认完成、取消订单)"""
        user_id = get_jwt_identity()
        action_data = request.json
        
        # Determine user_role for service layer, similar to OrderListResource
        jwt_user = User.query.get(user_id)
        if not jwt_user:
            raise NotFoundException("用户不存在。")
        user_role = jwt_user.current_role
        if not user_role:
             raise InvalidUsageException("无法确定用户角色以执行操作。")

        try:
            updated_order = order_service.process_order_action(order_id, user_id, user_role, action_data)
            order_data = OrderSchema().dump(updated_order)
            return api_success_response(order_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            # Log e
            raise BusinessException(message=f"订单操作失败: {str(e)}", status_code=500)

@ns.route('/<int:order_id>/actual_times')
@ns.param('order_id', '订单ID')
class OrderActualTimesResource(Resource):
    @jwt_required()
    @ns.expect(order_time_update_input_model)
    @ns.response(200, '更新实际工作时间成功', model=order_output_model)
    @ns.response(400, '无效输入或时间错误')
    @ns.response(403, '无权更新此订单时间')
    @ns.response(404, '订单未找到')
    def put(self, order_id):
        """(若独立) 更新订单的实际工作开始和结束时间 (通常零工操作)"""
        user_id = get_jwt_identity()
        data = request.json
        try:
            # OrderTimeUpdateSchema().load(data) # Can be used for Marshmallow-level validation first
            updated_order = order_service.update_order_actual_times(order_id, user_id, data)
            order_data = OrderSchema().dump(updated_order)
            return api_success_response(order_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            # Log e
            raise BusinessException(message=f"更新订单实际时间失败: {str(e)}", status_code=500) 