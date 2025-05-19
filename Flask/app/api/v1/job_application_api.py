from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.job_application_service import job_application_service
from ...schemas import JobApplicationSchema
from ...schemas import UserPublicSchema # For embedding freelancer info
from ...schemas import JobSchema # For embedding job info
from ...models.job import JobApplicationStatusEnum # Corrected import: For status enum
from ...utils.exceptions import BusinessException, NotFoundException, InvalidUsageException, AuthorizationException
from ...utils.helpers import api_success_response

ns = Namespace('job_applications', description='工作申请相关操作')

# --- API Models for JobApplication --- (Align with JobApplicationSchema)
# Reusing UserPublicOutput from auth_api or defining a specific one
# from .auth_api import user_public_output_model
# For now, using fields directly for brevity or assuming UserPublicSchema covers it.

freelancer_applicant_info_model = ns.model('FreelancerApplicantInfo', {
    'id': fields.Integer(readonly=True, description='用户ID'),
    'nickname': fields.String(readonly=True, description='用户昵称'), # From User or Profile
    'avatar_url': fields.String(readonly=True, description='用户头像URL') # From User or Profile
    # Potentially add a link to full freelancer profile if needed
})

job_summary_model = ns.model('JobSummaryForApplicationOutput', {
    'id': fields.Integer(readonly=True, description='工作ID'),
    'title': fields.String(readonly=True, description='工作标题')
})

job_application_output_model = ns.model('JobApplicationOutput', {
    'id': fields.Integer(readonly=True, description='申请唯一ID'),
    'job_id': fields.Integer(readonly=True, description='工作ID'),
    'freelancer_user_id': fields.Integer(readonly=True, description='申请人用户ID'),
    'employer_user_id': fields.Integer(readonly=True, description='雇主用户ID'), # Added based on service layer enrichment
    'freelancer_info': fields.Nested(freelancer_applicant_info_model, readonly=True, description='申请人简要信息', skip_none=True),
    'job_info': fields.Nested(job_summary_model, readonly=True, description='工作简要信息', skip_none=True), # Embed job summary
    'application_message': fields.String(description='申请留言'),
    'status': fields.String(readonly=True, description='申请状态'),
    'rejection_reason': fields.String(readonly=True, description='拒绝原因'),
    'created_at': fields.DateTime(readonly=True, description='申请提交时间'),
    'processed_at': fields.DateTime(readonly=True, description='状态更新时间/处理时间') # Consistent naming
})

job_application_creation_input_model = ns.model('JobApplicationCreationInput', { # Was job_application_input_model
    'application_message': fields.String(description='申请留言 (可选)')
})

# 4. Model for PUT /<id>/process
job_application_process_input_model = ns.model('JobApplicationProcessInput', {
    'status': fields.String(required=True, description='新的申请状态', enum=[JobApplicationStatusEnum.accepted.value, JobApplicationStatusEnum.rejected.value]),
    'reason': fields.String(description='原因 (例如拒绝原因，可选)')
})

job_application_cancel_input_model = ns.model('JobApplicationCancelInput', { # Was application_status_update_input_model for cancel
    'reason': fields.String(description='取消原因 (可选)')
})

# 5. Pagination structure update
pagination_info_model = ns.model('PaginationInfo', {
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_pages': fields.Integer(description='总页数'),
    'total_items': fields.Integer(description='总条目数')
})

paginated_application_response_model = ns.model('PaginatedJobApplicationResponse', { # Was paginated_application_model
    'items': fields.List(fields.Nested(job_application_output_model)),
    'pagination': fields.Nested(pagination_info_model) # Nested pagination
})

application_list_parser = reqparse.RequestParser()
application_list_parser.add_argument('page', type=int, location='args', default=1, help='页码')
application_list_parser.add_argument('per_page', type=int, location='args', default=10, help='每页数量')
application_list_parser.add_argument('status', type=str, location='args', help='按状态筛选申请')

check_application_parser = reqparse.RequestParser()
check_application_parser.add_argument('job_id', type=int, required=True, location='args', help='工作ID')

@ns.route('/check')
class CheckApplicationStatusResource(Resource):
    @jwt_required()
    @ns.expect(check_application_parser)
    @ns.response(200, '检查申请状态成功')
    def get(self):
        """检查当前用户是否已申请特定工作"""
        user_id = get_jwt_identity()
        args = check_application_parser.parse_args()
        job_id = args['job_id']
        try:
            is_applied = job_application_service.has_user_applied_for_job(user_id, job_id)
            return api_success_response(data={'has_applied': is_applied}, message="Successfully checked application status.")
        except NotFoundException as e: # More specific exception handling
            # If job_application_service.has_user_applied_for_job raises NotFoundException when no application found for a valid job
            # or if the job itself is not found, this might be one way to handle it.
            # However, for a 'check' endpoint, usually not finding an application means 'has_applied: false'
            # rather than a 404, unless the job_id itself is invalid.
            # Assuming the service handles "no application found" gracefully by returning false.
            # This catch block is more for if the job_id is invalid or other "not found" scenarios.
            raise NotFoundException(f"Resource not found or error checking status: {str(e)}")
        except BusinessException as e: # Catch other business logic errors
            raise BusinessException(f"Business error checking application status: {str(e)}")
        except Exception as e:
            # Log the exception e for debugging
            # logger.error(f"Unexpected error checking application status: {str(e)}")
            raise InvalidUsageException(f"Error checking application status: {str(e)}")


@ns.route('/jobs/<int:job_id>/apply')
@ns.param('job_id', '目标工作ID')
class ApplyToJobResource(Resource):
    @jwt_required()
    @ns.expect(job_application_creation_input_model)
    @ns.response(201, '申请提交成功', model=job_application_output_model)
    def post(self, job_id):
        """零工用户申请特定工作"""
        freelancer_user_id = get_jwt_identity()
        data = request.json or {}
        try:
            # Service method renamed
            application = job_application_service.create_job_application(freelancer_user_id, job_id, data)
            application_data = JobApplicationSchema().dump(application)
            return api_success_response(application_data, 201)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            # Ensure consistent error code for unexpected issues
            raise BusinessException(message=f"申请工作时发生意外错误: {str(e)}", status_code=500, error_code=50000)

@ns.route('/jobs/<int:job_id>/list') # Path kept, similar to above. Doc is GET /jobs/{job_id}/applications
@ns.param('job_id', '目标工作ID')
class JobApplicationsListForEmployerResource(Resource):
    @jwt_required()
    @ns.expect(application_list_parser)
    @ns.response(200, '获取工作申请列表成功', model=paginated_application_response_model)
    def get(self, job_id):
        """雇主查看其发布工作的申请列表 (分页)"""
        employer_user_id = get_jwt_identity()
        args = application_list_parser.parse_args()
        filters = {'status': args.get('status')} # Pass status filter
        try:
            paginated_apps = job_application_service.get_applications_for_job(
                job_id, employer_user_id, page=args['page'], per_page=args['per_page'], filters=filters
            )
            items_data = JobApplicationSchema(many=True, context={'include_freelancer_info': True}).dump(paginated_apps.items)
            # Updated pagination structure
            return api_success_response({
                'items': items_data,
                'pagination': {
                    'page': paginated_apps.page,
                    'per_page': paginated_apps.per_page,
                    'total_pages': paginated_apps.pages,
                    'total_items': paginated_apps.total
                }
            })
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取工作申请列表时发生意外错误: {str(e)}", status_code=500, error_code=50000)

@ns.route('/my') 
class FreelancerMyApplicationsListResource(Resource): # Renamed from FreelancerApplicationsListResource
    @jwt_required()
    @ns.expect(application_list_parser)
    @ns.response(200, '获取我的申请列表成功', model=paginated_application_response_model)
    def get(self):
        """零工用户查看自己提交的申请列表 (分页)"""
        freelancer_user_id = get_jwt_identity()
        args = application_list_parser.parse_args()
        filters = {'status': args.get('status')} # Pass status filter
        try:
            # Service method renamed
            paginated_apps = job_application_service.get_applications_by_freelancer(
                freelancer_user_id, page=args['page'], per_page=args['per_page'], filters=filters
            )
            # Embed job_info for freelancer's view
            items_data = JobApplicationSchema(many=True, context={'include_job_info': True}).dump(paginated_apps.items)
            # Updated pagination structure
            return api_success_response({
                'items': items_data,
                'pagination': {
                    'page': paginated_apps.page,
                    'per_page': paginated_apps.per_page,
                    'total_pages': paginated_apps.pages,
                    'total_items': paginated_apps.total
                }
            })
        except (NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取我的申请列表时发生意外错误: {str(e)}", status_code=500, error_code=50000)

@ns.route('/<int:application_id>')
@ns.param('application_id', '申请ID')
class JobApplicationDetailResource(Resource):
    @jwt_required()
    @ns.response(200, '获取申请详情成功', model=job_application_output_model)
    def get(self, application_id):
        """获取单个申请详情 (申请人或相关雇主可访问)"""
        current_user_id = get_jwt_identity()
        try:
            application = job_application_service.get_application_by_id(application_id, current_user_id)
            # Ensure context for schema includes all relevant nested info
            application_data = JobApplicationSchema(context={'include_freelancer_info': True, 'include_job_info': True}).dump(application)
            return api_success_response(application_data)
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取申请详情失败: {str(e)}", status_code=500, error_code=50000)

@ns.route('/<int:application_id>/process')
@ns.param('application_id', '申请ID')
class ProcessApplicationResource(Resource):
    @jwt_required()
    @ns.expect(job_application_process_input_model)
    @ns.response(200, '处理申请成功', model=job_application_output_model)
    @ns.doc(description="雇主处理申请 (接受/拒绝)。")
    def put(self, application_id):
        """雇主处理工作申请 (接受/拒绝)"""
        employer_user_id = get_jwt_identity()
        data = request.json
        new_status = data.get('status')
        reason = data.get('reason')
        try:
            # service层可能返回包含application和order的字典
            result = job_application_service.process_application(application_id, employer_user_id, new_status, reason)
            
            # 从结果中获取application
            application = result.get('application')
            if not application:
                raise BusinessException(message="处理申请后未返回应用对象", status_code=500)
            
            # 序列化application对象
            application_data = JobApplicationSchema().dump(application)
            
            # 如果创建了订单，将订单ID添加到响应中
            if result.get('order'):
                application_data['created_order_id'] = result['order'].id

            return api_success_response(application_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"处理申请时发生意外错误: {str(e)}", status_code=500, error_code=50000)

@ns.route('/<int:application_id>/cancel')
@ns.param('application_id', '申请ID')
class CancelApplicationResource(Resource):
    @jwt_required()
    @ns.expect(job_application_cancel_input_model) # Use specific cancel input model
    @ns.response(200, '取消申请成功', model=job_application_output_model)
    def post(self, application_id):
        """零工用户取消自己的工作申请"""
        freelancer_user_id = get_jwt_identity()
        data = request.json or {}
        reason = data.get('reason')
        try:
            application = job_application_service.cancel_application_by_freelancer(application_id, freelancer_user_id, reason)
            application_data = JobApplicationSchema().dump(application)
            return api_success_response(application_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"取消申请时发生意外错误: {str(e)}", status_code=500, error_code=50000)