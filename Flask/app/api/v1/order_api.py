from flask_restx import Namespace, Resource, fields, reqparse
from flask import current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
import uuid

from ...services.order_service import order_service
from ...schemas.order_schema import OrderSchema, OrderActionSchema, OrderTimeUpdateSchema
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthorizationException
from ...utils.helpers import api_success_response
from ...models.user import User # To get current_user role
from sqlalchemy import func

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

# --- 辅助函数，获取查询计数，兼容不同版本SQLAlchemy ---
def _get_query_count(query):
    """获取查询结果计数，兼容不同版本SQLAlchemy"""
    try:
        # SQLAlchemy 1.4+ 推荐用法
        return query.count()
    except (TypeError, AttributeError):
        # 回退到老方法
        current_app.logger.debug("[OrderAPI] 回退到使用func.count() 计算查询结果")
        count_q = query.statement.with_only_columns([func.count()]).order_by(None)
        return query.session.execute(count_q).scalar()

# --- Routes ---
@ns.route('/')
class OrderListResource(Resource):
    @jwt_required()
    @ns.expect(order_list_parser)
    @ns.response(200, '获取订单列表成功', model=paginated_order_model)
    def get(self):
        """用户获取自己的订单列表 (根据角色区分是零工还是雇主)"""
        user_identity = get_jwt_identity() # This is likely a UUID string
        current_app.logger.info(f"[OrderAPI] GET /orders - JWT Identity: {user_identity}")
        args = order_list_parser.parse_args()
        current_app.logger.info(f"[OrderAPI] Request args: {args}")
        
        user_role_arg = args.get('role')
        
        # 详细记录用户查询过程
        current_app.logger.info(f"[OrderAPI] Attempting to find user with identity: {user_identity}")
        
        jwt_user = None
        
        # 尝试作为UUID查找
        try:
            if isinstance(user_identity, str) and len(user_identity) > 30:  # 看起来像UUID
                current_app.logger.debug(f"[OrderAPI] Trying to find user by UUID: {user_identity}")
                jwt_user = User.query.filter_by(uuid=user_identity).first()
                if jwt_user:
                    current_app.logger.info(f"[OrderAPI] User found by UUID: {user_identity}, ID: {jwt_user.id}")
        except Exception as e:
            current_app.logger.warning(f"[OrderAPI] Error finding user by UUID: {str(e)}")
            
        # 尝试作为ID查找
        if not jwt_user:
            try:
                current_app.logger.debug(f"[OrderAPI] Trying to find user by ID: {user_identity}")
                # 尝试将身份转换为整数ID
                user_id = int(user_identity) if isinstance(user_identity, str) else user_identity
                jwt_user = User.query.get(user_id)
                if jwt_user:
                    current_app.logger.info(f"[OrderAPI] User found by ID: {user_id}")
            except (ValueError, TypeError) as e:
                current_app.logger.warning(f"[OrderAPI] Error finding user by ID: {str(e)}")

        # 仍未找到用户
        if not jwt_user:
            current_app.logger.error(f"[OrderAPI] User not found with identity: {user_identity}")
            raise NotFoundException("用户不存在或身份无法识别。", error_code=40401)
        
        # 记录用户角色信息
        current_app.logger.info(f"[OrderAPI] User {jwt_user.id} roles - current: {jwt_user.current_role}, available: {jwt_user.available_roles}")
        
        user_role_to_use = user_role_arg if user_role_arg else jwt_user.current_role
        
        if not user_role_to_use:
            current_app.logger.warning(f"[OrderAPI] Could not determine role for user {jwt_user.id}")
            raise InvalidUsageException("无法确定用户角色。请提供 'role' 参数或确保用户已设置当前角色。")
            
        current_app.logger.info(f"[OrderAPI] Using role: {user_role_to_use} for user {jwt_user.id}")

        filters = {'status': args.get('status')}
        filters = {k: v for k, v in filters.items() if v is not None}
        current_app.logger.info(f"[OrderAPI] Applying filters: {filters}")

        try:
            current_app.logger.info(f"[OrderAPI] Calling order_service.get_orders_for_user with user_id={jwt_user.id}, role={user_role_to_use}")
            paginated_orders = order_service.get_orders_for_user(
                user_id=jwt_user.id, # Pass the integer ID of the fetched user
                user_role=user_role_to_use,
                filters=filters,
                page=args.get('page'),
                per_page=args.get('per_page')
            )
            current_app.logger.info(f"[OrderAPI] Got {len(paginated_orders.items)} orders")
            order_data = OrderSchema(many=True).dump(paginated_orders.items)
            current_app.logger.info(f"[OrderAPI] Serialized {len(order_data)} orders")
            return api_success_response({
                'items': order_data,
                'page': paginated_orders.page,
                'per_page': paginated_orders.per_page,
                'total_pages': paginated_orders.pages,
                'total_items': paginated_orders.total
            })
        except (AuthorizationException, InvalidUsageException, BusinessException) as e:
            current_app.logger.error(f"[OrderAPI] Known error: {str(e)}")
            raise e
        except Exception as e:
            # Log e
            current_app.logger.error(f"[OrderAPI] Unexpected error: {str(e)}", exc_info=True)
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

# # --- Debug/Test Route (仅限开发环境) ---
# @ns.route('/debug/create-test-order')
# class OrderTestResource(Resource):
#     @jwt_required()
#     @ns.response(200, '创建测试订单成功', model=order_output_model)
#     def post(self):
#         """[开发环境] 为当前用户创建测试订单"""
#         # 只在开发环境中启用
#         if not current_app.config.get('DEBUG', False):
#             return {"message": "此接口仅在开发环境中可用"}, 403
        
#         try:
#             user_identity = get_jwt_identity()
#             current_app.logger.info(f"[OrderAPI-Debug] 创建测试订单请求, JWT Identity: {user_identity}")
            
#             # 获取用户
#             jwt_user = User.query.filter_by(uuid=str(user_identity)).first()
#             if not jwt_user:
#                 try:
#                     user_id_as_int = int(user_identity)
#                     jwt_user = User.query.get(user_id_as_int)
#                 except (ValueError, TypeError):
#                     pass
                    
#             if not jwt_user:
#                 current_app.logger.error("[OrderAPI-Debug] 用户不存在")
#                 return {"message": "用户不存在"}, 404
            
#             # 确定角色
#             user_role = jwt_user.current_role
#             if not user_role:
#                 current_app.logger.error("[OrderAPI-Debug] 用户未设置角色")
#                 return {"message": "用户未设置角色"}, 400
                
#             # 根据角色创建测试订单
#             current_app.logger.info(f"[OrderAPI-Debug] 用户角色: {user_role}")
            
#             if user_role == 'employer':
#                 # 查找一个零工用户
#                 freelancer_user = User.query.filter_by(current_role='freelancer').first()
#                 if not freelancer_user:
#                     current_app.logger.error("[OrderAPI-Debug] 未找到零工用户")
#                     return {"message": "系统中没有零工用户，无法创建测试订单"}, 400
                
#                 # 为雇主创建一个测试工作
#                 from ...models.job import Job, JobStatusEnum
#                 import random
#                 from datetime import datetime, timedelta
                
#                 # 创建一个测试工作
#                 job = Job(
#                     employer_user_id=jwt_user.id,
#                     title=f"测试工作 #{random.randint(1000, 9999)}",
#                     description="这是一个自动生成的测试工作",
#                     job_category="tech",
#                     location_address="测试地址",
#                     location_city="测试城市",
#                     start_time=datetime.now() + timedelta(days=1),
#                     end_time=datetime.now() + timedelta(days=2),
#                     salary_amount=random.randint(100, 1000),
#                     salary_type="daily",
#                     required_people=1,
#                     status=JobStatusEnum.open.value
#                 )
#                 db.session.add(job)
#                 db.session.flush()  # 获取job.id
                
#                 # 直接从服务创建订单
#                 test_order = Order(
#                     job_id=job.id,
#                     freelancer_user_id=freelancer_user.id,
#                     employer_user_id=jwt_user.id,
#                     order_amount=job.salary_amount,
#                     platform_fee=job.salary_amount * 0.1,
#                     freelancer_income=job.salary_amount * 0.9,
#                     start_time_scheduled=job.start_time,
#                     end_time_scheduled=job.end_time,
#                     status=OrderStatusEnum.pending_start.value,
#                     freelancer_confirmation_status=ConfirmationStatusEnum.pending.value,
#                     employer_confirmation_status=ConfirmationStatusEnum.confirmed.value
#                 )
                
#             elif user_role == 'freelancer':
#                 # 查找一个雇主用户
#                 employer_user = User.query.filter_by(current_role='employer').first()
#                 if not employer_user:
#                     current_app.logger.error("[OrderAPI-Debug] 未找到雇主用户")
#                     return {"message": "系统中没有雇主用户，无法创建测试订单"}, 400
                
#                 # 为零工创建一个测试订单
#                 from ..models.job import Job, JobStatusEnum
#                 import random
#                 from datetime import datetime, timedelta
                
#                 # 创建一个测试工作
#                 job = Job(
#                     employer_user_id=employer_user.id,
#                     title=f"测试工作 #{random.randint(1000, 9999)}",
#                     description="这是一个自动生成的测试工作",
#                     job_category="tech",
#                     location_address="测试地址",
#                     location_city="测试城市",
#                     start_time=datetime.now() + timedelta(days=1),
#                     end_time=datetime.now() + timedelta(days=2),
#                     salary_amount=random.randint(100, 1000),
#                     salary_type="daily",
#                     required_people=1,
#                     status=JobStatusEnum.open.value
#                 )
#                 db.session.add(job)
#                 db.session.flush()  # 获取job.id
                
#                 # 直接从服务创建订单
#                 test_order = Order(
#                     job_id=job.id,
#                     freelancer_user_id=jwt_user.id,
#                     employer_user_id=employer_user.id,
#                     order_amount=job.salary_amount,
#                     platform_fee=job.salary_amount * 0.1,
#                     freelancer_income=job.salary_amount * 0.9,
#                     start_time_scheduled=job.start_time,
#                     end_time_scheduled=job.end_time,
#                     status=OrderStatusEnum.pending_start.value,
#                     freelancer_confirmation_status=ConfirmationStatusEnum.pending.value,
#                     employer_confirmation_status=ConfirmationStatusEnum.confirmed.value
#                 )
#             else:
#                 return {"message": f"不支持的用户角色: {user_role}"}, 400
                
#             # 保存订单
#             db.session.add(test_order)
#             db.session.commit()
            
#             # 返回订单详情
#             order_data = OrderSchema().dump(test_order)
#             current_app.logger.info(f"[OrderAPI-Debug] 成功创建测试订单 ID: {test_order.id}")
#             return api_success_response(order_data)
            
#         except Exception as e:
#             db.session.rollback()
#             current_app.logger.error(f"[OrderAPI-Debug] 创建测试订单失败: {str(e)}", exc_info=True)
#             return {"message": f"创建测试订单失败: {str(e)}"}, 500 