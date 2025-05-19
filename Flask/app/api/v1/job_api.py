from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.job_service import job_service
from ...schemas.job_schema import JobSchema, JobRequiredSkillSchema
from ...models.job import JobStatusEnum # For status enum if needed in API layer
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthorizationException
from ...utils.helpers import api_success_response

ns = Namespace('jobs', description='工作信息相关操作')

# --- API Models for Job --- 
geopoint_model = ns.model('GeoPoint', {
    'type': fields.String(required=True, description='GeoJSON type, e.g., Point', example='Point'),
    'coordinates': fields.List(fields.Float, required=True, description='Coordinates [longitude, latitude]', example=[118.10, 24.46])
})

job_output_model = ns.model('JobOutput', {
    'id': fields.Integer(readonly=True, description='工作唯一ID'),
    'employer_user_id': fields.Integer(readonly=True, description='发布者用户ID'),
    'title': fields.String(required=True, description='工作标题', example='周末兼职传单派发员'),
    'description': fields.String(required=True, description='工作描述', example='负责在指定区域派发宣传单页...'),
    'job_category': fields.String(required=True, description='工作类别', example='派发'),
    'job_tags': fields.List(fields.String, description='工作标签', example=['日结', '学生兼职']),
    'location_address': fields.String(required=True, description='详细工作地点', example='厦门市思明区XX路XX号'),
    'location_province': fields.String(description='省份'),
    'location_city': fields.String(description='城市'),
    'location_district': fields.String(description='区县'),
    'location_point': fields.Nested(geopoint_model, description='地理坐标 (GeoJSON)'),
    'start_time': fields.DateTime(required=True, description='预计开始时间 (ISO 8601)', example='2025-05-10T09:00:00+08:00'),
    'end_time': fields.DateTime(required=True, description='预计结束时间 (ISO 8601)', example='2025-05-10T17:00:00+08:00'),
    'salary_amount': fields.Float(required=True, description='薪资金额', example=150.00),
    'salary_type': fields.String(required=True, description='计薪方式', enum=['hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable'], example='fixed'),
    'salary_negotiable': fields.Boolean(description='薪资是否可议', default=False),
    'required_people': fields.Integer(required=True, description='需求人数', example=5),
    'accepted_people': fields.Integer(readonly=True, description='已接受人数'),
    'skill_requirements': fields.String(description='技能要求描述'),
    'is_urgent': fields.Boolean(description='是否急聘', default=False),
    'status': fields.String(readonly=True, description='工作状态'),
    'cancellation_reason': fields.String(readonly=True, description='取消原因'),
    'view_count': fields.Integer(readonly=True, description='浏览次数'),
    'application_deadline': fields.DateTime(description='报名截止时间 (ISO 8601)'),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'updated_at': fields.DateTime(readonly=True, description='更新时间')
})

job_creation_input_model = ns.model('JobCreationInput', {
    'title': fields.String(required=True, description='工作标题'),
    'description': fields.String(required=True, description='工作描述'),
    'job_category': fields.String(required=True, description='工作类别'),
    'job_tags': fields.List(fields.String, description='工作标签 (可选)'),
    'location_address': fields.String(required=True, description='详细工作地点'),
    'location_province': fields.String(description='省份 (可选)'),
    'location_city': fields.String(description='城市 (可选)'),
    'location_district': fields.String(description='区县 (可选)'),
    'latitude': fields.Float(description='纬度 (可选, 用于生成location_point)'),
    'longitude': fields.Float(description='经度 (可选, 用于生成location_point)'),
    'location_point': fields.Nested(geopoint_model, description='地理坐标 (GeoJSON, 如果直接提供) (可选)'),
    'start_time': fields.DateTime(required=True, description='预计开始时间 (ISO 8601)'),
    'end_time': fields.DateTime(required=True, description='预计结束时间 (ISO 8601)'),
    'salary_amount': fields.Float(required=True, description='薪资金额'),
    'salary_type': fields.String(required=True, description='计薪方式', enum=['hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable']),
    'salary_negotiable': fields.Boolean(description='薪资是否可议', default=False),
    'required_people': fields.Integer(required=True, description='需求人数'),
    'skill_requirements': fields.String(description='技能要求描述 (可选)'),
    'is_urgent': fields.Boolean(description='是否急聘', default=False),
    'application_deadline': fields.DateTime(description='报名截止时间 (可选, ISO 8601)')
})

job_update_input_model = ns.model('JobUpdateInput', {
    'title': fields.String(description='工作标题'),
    'description': fields.String(description='工作描述'),
    'job_category': fields.String(description='工作类别'),
    'job_tags': fields.List(fields.String, description='工作标签'),
    'location_address': fields.String(description='详细工作地点'),
    'location_province': fields.String(description='省份'),
    'location_city': fields.String(description='城市'),
    'location_district': fields.String(description='区县'),
    'latitude': fields.Float(description='纬度 (可选, 用于更新location_point)'),
    'longitude': fields.Float(description='经度 (可选, 用于更新location_point)'),
    'location_point': fields.Nested(geopoint_model, description='地理坐标 (GeoJSON, 如果直接提供)'),
    'start_time': fields.DateTime(description='预计开始时间 (ISO 8601)'),
    'end_time': fields.DateTime(description='预计结束时间 (ISO 8601)'),
    'salary_amount': fields.Float(description='薪资金额'),
    'salary_type': fields.String(description='计薪方式', enum=['hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable']),
    'salary_negotiable': fields.Boolean(description='薪资是否可议'),
    'required_people': fields.Integer(description='需求人数'),
    'skill_requirements': fields.String(description='技能要求描述'),
    'is_urgent': fields.Boolean(description='是否急聘'),
    'application_deadline': fields.DateTime(description='报名截止时间 (ISO 8601)'),
    'status': fields.String(description='工作状态 (特定状态可修改)', enum=[s.value for s in JobStatusEnum])
})

pagination_model = ns.model('Pagination', {
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_pages': fields.Integer(description='总页数'),
    'total_items': fields.Integer(description='总条目数')
})

paginated_job_response_model = ns.model('PaginatedJobResponse', {
    'items': fields.List(fields.Nested(job_output_model)),
    'pagination': fields.Nested(pagination_model)
})

job_list_parser = reqparse.RequestParser()
job_list_parser.add_argument('page', type=int, location='args', default=1, help='页码')
job_list_parser.add_argument('per_page', type=int, location='args', default=10, help='每页数量')
job_list_parser.add_argument('q', type=str, location='args', help='关键词搜索 (标题, 描述)')
job_list_parser.add_argument('status', type=str, location='args', help=f"工作状态 (e.g., {', '.join([s.value for s in JobStatusEnum])})")
job_list_parser.add_argument('job_category', type=str, location='args', help='工作类别')
job_list_parser.add_argument('location_province', type=str, location='args', help='省份')
job_list_parser.add_argument('location_city', type=str, location='args', help='城市')
job_list_parser.add_argument('location_district', type=str, location='args', help='区县')
job_list_parser.add_argument('latitude', type=float, location='args', help='纬度 (用于地理范围搜索)')
job_list_parser.add_argument('longitude', type=float, location='args', help='经度 (用于地理范围搜索)')
job_list_parser.add_argument('radius_km', type=float, location='args', help='半径 (公里, 用于地理范围搜索)')
job_list_parser.add_argument('salary_min', type=float, location='args', help='最低薪资')
job_list_parser.add_argument('salary_max', type=float, location='args', help='最高薪资')
job_list_parser.add_argument('salary_type', type=str, location='args', help='计薪方式')
job_list_parser.add_argument('job_tags', type=str, location='args', help='工作标签 (逗号分隔)') # Consider action='append' for multiple tags
job_list_parser.add_argument('is_urgent', type=bool, location='args', help='是否急聘')
job_list_parser.add_argument('start_time_from', type=str, location='args', help='开始时间不早于 (ISO 8601)')
job_list_parser.add_argument('start_time_to', type=str, location='args', help='开始时间不晚于 (ISO 8601)')
job_list_parser.add_argument('sort_by', type=str, location='args', help='排序字段 (e.g., created_at_desc, salary_amount_asc)')
job_list_parser.add_argument('employer_user_id', type=int, location='args', help='发布者ID (用于查看特定雇主的工作)') # Keep for admin or direct lookup

my_posted_jobs_parser = reqparse.RequestParser()
my_posted_jobs_parser.add_argument('page', type=int, location='args', default=1, help='页码')
my_posted_jobs_parser.add_argument('per_page', type=int, location='args', default=10, help='每页数量')
my_posted_jobs_parser.add_argument('status', type=str, location='args', help='工作状态')
my_posted_jobs_parser.add_argument('sort_by', type=str, location='args', help='排序字段')

recommended_jobs_parser = reqparse.RequestParser()
recommended_jobs_parser.add_argument('count', type=int, location='args', default=10, help='推荐数量')


@ns.route('')
class JobListResource(Resource):
    @ns.expect(job_list_parser)
    @ns.response(200, '获取工作列表成功', model=paginated_job_response_model)
    def get(self):
        """获取工作列表 (支持筛选和分页)"""
        args = job_list_parser.parse_args()
        page = args.pop('page')
        per_page = args.pop('per_page')
        sort_by_arg = args.pop('sort_by', None) # แยก sort_by ออก
        
        filters = {k: v for k, v in args.items() if v is not None}
        try:
            paginated_jobs = job_service.search_jobs(filters=filters, sort_by=sort_by_arg, page=page, per_page=per_page)
            items_data = JobSchema(many=True).dump(paginated_jobs.items)
            return api_success_response({
                'items': items_data,
                'pagination': {
                    'page': paginated_jobs.page,
                    'per_page': paginated_jobs.per_page,
                    'total_pages': paginated_jobs.pages,
                    'total_items': paginated_jobs.total
                }
            })
        except Exception as e:
            raise BusinessException(message=f"获取工作列表失败: {str(e)}", status_code=500, error_code=50001)

    @jwt_required()
    @ns.expect(job_creation_input_model)
    @ns.response(201, '工作创建成功', model=job_output_model)
    def post(self):
        """雇主发布新工作"""
        employer_user_identity_from_token = get_jwt_identity()
        current_app.logger.info(f"[JobAPI] Attempting to create job. User identity from token: {employer_user_identity_from_token}, type: {type(employer_user_identity_from_token)}")

        data = request.json
        try:
            # Pass the UUID string directly to the service layer
            new_job = job_service.create_job(employer_user_identity=employer_user_identity_from_token, data=data)
            # 使用api_success_response包装结果，确保响应格式一致
            job_data = JobSchema().dump(new_job)
            return api_success_response(job_data, status_code=201)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            current_app.logger.error(f"[JobAPI] Error creating job: {getattr(e, 'message', str(e))} (Code: {getattr(e, 'error_code', 'N/A')})", exc_info=True)
            raise
        except Exception as e:
            current_app.logger.error(f"[JobAPI] Unexpected error creating job: {str(e)}", exc_info=True)
            raise BusinessException(message="创建工作时发生意外服务错误。", status_code=500)

@ns.route('/<int:job_id>')
@ns.param('job_id', '工作ID')
class JobResource(Resource):
    @ns.response(200, '获取工作详情成功', model=job_output_model)
    def get(self, job_id):
        """获取指定ID的工作详情 (浏览次数会增加)"""
        try:
            job = job_service.get_job_by_id(job_id, increment_view_count=True)
            job_data = JobSchema().dump(job)
            return api_success_response(job_data)
        except (NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取工作详情失败: {str(e)}", status_code=500, error_code=50001)

    @jwt_required()
    @ns.expect(job_update_input_model)
    @ns.response(200, '工作信息更新成功', model=job_output_model)
    def put(self, job_id):
        """更新指定ID的工作信息 (仅限发布者)"""
        employer_user_id = get_jwt_identity()
        data = request.json
        try:
            updated_job = job_service.update_job(job_id, employer_user_id, data)
            job_data = JobSchema().dump(updated_job)
            return api_success_response(job_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"更新工作失败: {str(e)}", status_code=500, error_code=50001)

    @jwt_required()
    @ns.response(200, '工作删除成功') 
    @ns.doc(description="删除指定ID的工作 (逻辑删除，状态变更为cancelled)。仅限发布者。")
    def delete(self, job_id):
        """删除指定ID的工作 (逻辑删除)"""
        employer_user_id = get_jwt_identity()
        try:
            # Add reason if desired from request or default
            # reason = request.json.get('reason', '由发布者删除') if request.is_json else '由发布者删除'
            job_service.delete_job(job_id, employer_user_id) # reason can be added to service call
            return api_success_response(None, message="工作删除成功") # API规范文档:成功时data可为null
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"删除工作失败: {str(e)}", status_code=500, error_code=50001)

@ns.route('/<int:job_id>/close')
@ns.param('job_id', '工作ID')
class JobCloseResource(Resource):
    @jwt_required()
    @ns.response(200, '工作关闭成功', model=job_output_model)
    @ns.doc(description="雇主关闭工作招聘 (将状态改为 filled)。仅限工作发布者。")
    def post(self, job_id):
        """雇主关闭工作招聘"""
        employer_user_id = get_jwt_identity()
        # reason = request.json.get('reason', '招聘结束') if request.is_json else '招聘结束' # Optional reason
        try:
            closed_job = job_service.close_job_listing(job_id, employer_user_id)
            job_data = JobSchema().dump(closed_job)
            return api_success_response(job_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"关闭工作失败: {str(e)}", status_code=500)

@ns.route('/<int:job_id>/duplicate')
@ns.param('job_id', '要复制的工作ID')
class JobDuplicateResource(Resource):
    @jwt_required()
    @ns.response(201, '工作复制成功', model=job_output_model)
    @ns.doc(description="雇主复制现有工作以快速创建新工作。新工作将处于待审核状态。仅限工作发布者。")
    def post(self, job_id):
        """雇主复制工作"""
        employer_user_id = get_jwt_identity()
        try:
            duplicated_job = job_service.duplicate_job(job_id, employer_user_id)
            job_data = JobSchema().dump(duplicated_job)
            return api_success_response(job_data, status_code=201)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"复制工作失败: {str(e)}", status_code=500)

@ns.route('/my_posted')
class MyPostedJobsResource(Resource):
    @jwt_required()
    @ns.expect(my_posted_jobs_parser)
    @ns.response(200, '获取我发布的工作列表成功', model=paginated_job_response_model)
    def get(self):
        """雇主获取自己发布的工作列表"""
        employer_user_id = get_jwt_identity()
        args = my_posted_jobs_parser.parse_args()
        page = args.pop('page')
        per_page = args.pop('per_page')
        sort_by_arg = args.pop('sort_by', None)
        filters = {k: v for k, v in args.items() if v is not None}
        try:
            paginated_jobs = job_service.get_jobs_by_employer(
                employer_user_id, filters=filters, sort_by=sort_by_arg, page=page, per_page=per_page
            )
            items_data = JobSchema(many=True).dump(paginated_jobs.items)
            return api_success_response({
                'items': items_data,
                'pagination': {
                    'page': paginated_jobs.page,
                    'per_page': paginated_jobs.per_page,
                    'total_pages': paginated_jobs.pages,
                    'total_items': paginated_jobs.total
                }
            })
        except Exception as e:
            raise BusinessException(message=f"获取我发布的工作列表失败: {str(e)}", status_code=500)

@ns.route('/recommendations')
class RecommendedJobsResource(Resource):
    @jwt_required() # Assuming recommendations are for logged-in freelancers
    @ns.expect(recommended_jobs_parser)
    @ns.response(200, '获取推荐工作列表成功', model=ns.model('RecommendedJobsResponse', {
        'items': fields.List(fields.Nested(job_output_model))
    })) # Simpler response, no pagination for this example
    def get(self):
        """(零工) 获取个性化推荐工作列表"""
        freelancer_user_id = get_jwt_identity()
        args = recommended_jobs_parser.parse_args()
        try:
            recommended_jobs_list = job_service.get_recommended_jobs(freelancer_user_id, count=args['count'])
            items_data = JobSchema(many=True).dump(recommended_jobs_list)
            return api_success_response({'items': items_data})
        except (NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取推荐工作失败: {str(e)}", status_code=500)


# --- API Models for JobRequiredSkill ---
skill_output_for_job_req_model = ns.model('SkillOutputForJobReq', {
    'id': fields.Integer(readonly=True, description='技能ID'),
    'name': fields.String(readonly=True, description='技能名称'),
    'category': fields.String(readonly=True, description='技能分类')
})

job_required_skill_output_model = ns.model('JobRequiredSkillOutput', {
    'job_id': fields.Integer(readonly=True, description='工作ID'),
    'skill_id': fields.Integer(readonly=True, description='技能ID'),
    'is_mandatory': fields.Boolean(description='是否为必须技能'),
    'skill': fields.Nested(skill_output_for_job_req_model, description='技能详情')
})

job_required_skill_input_model = ns.model('JobRequiredSkillInput', {
    'skill_id': fields.Integer(required=True, description='技能ID'),
    'is_mandatory': fields.Boolean(description='是否为必须技能', default=True)
})

@ns.route('/<int:job_id>/required_skills')
@ns.param('job_id', '工作ID')
class JobRequiredSkillsResource(Resource):
    @jwt_required()
    @ns.expect(job_required_skill_input_model)
    @ns.response(201, '成功为工作添加技能要求', model=job_required_skill_output_model)
    @ns.doc(description="为指定工作添加一项技能要求。需要工作发布者权限。")
    def post(self, job_id):
        """为工作添加技能要求"""
        employer_user_id = get_jwt_identity()
        skill_data = request.json
        try:
            new_req_skill = job_service.add_required_skill_to_job(job_id, employer_user_id, skill_data)
            result_data = JobRequiredSkillSchema().dump(new_req_skill)
            return api_success_response(result_data, status_code=201)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"为工作添加技能要求失败: {str(e)}", status_code=500)

@ns.route('/<int:job_id>/required_skills/<int:skill_id>')
@ns.param('job_id', '工作ID')
@ns.param('skill_id', '要移除的技能ID')
class JobRequiredSkillDetailResource(Resource):
    @jwt_required()
    @ns.response(204, '成功移除工作的技能要求')
    @ns.doc(description="移除指定工作的某项技能要求。需要工作发布者权限。")
    def delete(self, job_id, skill_id):
        """移除工作的技能要求"""
        employer_user_id = get_jwt_identity()
        try:
            job_service.remove_required_skill_from_job(job_id, employer_user_id, skill_id)
            return api_success_response(None, status_code=204, message="技能要求移除成功")
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"移除工作技能要求失败: {str(e)}", status_code=500)