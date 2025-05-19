from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from ...services.verification_service import verification_service
from ...schemas import VerificationRecordSchema # Corrected import
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException
from ...utils.helpers import api_success_response

ns = Namespace('verifications', description='用户认证管理')

# API Model for VerificationRecord (align with VerificationRecordSchema)
verification_record_model = ns.model('VerificationRecordOutput', {
    'id': fields.Integer(readonly=True, description='认证记录ID'),
    'user_id': fields.Integer(readonly=True, description='用户ID'),
    'profile_type': fields.String(readonly=True, description='档案类型 (freelancer, employer_individual, employer_company)'),
    'submitted_data': fields.Raw(readonly=True, description='提交的认证资料 (JSON)'), # Sensitive data might be masked or limited in API output
    'status': fields.String(readonly=True, description='审核状态 (pending, approved, rejected)'),
    'reviewer_id': fields.Integer(readonly=True, description='审核管理员ID'),
    'reviewed_at': fields.DateTime(readonly=True, description='审核时间'),
    'rejection_reason': fields.String(readonly=True, description='拒绝原因'),
    'created_at': fields.DateTime(readonly=True, description='提交时间'),
    'updated_at': fields.DateTime(readonly=True, description='最后更新时间')
})

verification_submission_input_model = ns.model('VerificationSubmissionInput', {
    'profile_type': fields.String(required=True, description='申请认证的档案类型', enum=['freelancer', 'employer_individual', 'employer_company']),
    'submitted_data': fields.Raw(required=True, description='提交的认证资料 (JSON对象)', example={'real_name': '张三', 'id_card_number': '12345...', 'id_card_photo_front_url': 'http://...'}) # Example structure
})

# Parser for list arguments
verification_list_parser = reqparse.RequestParser()
verification_list_parser.add_argument('page', type=int, location='args', default=1, help='页码')
verification_list_parser.add_argument('per_page', type=int, location='args', default=10, help='每页数量')
verification_list_parser.add_argument('profile_type', type=str, location='args', help='筛选特定类型的认证记录 (freelancer, employer_individual, employer_company)')

# For paginated list of records
paginated_verification_model = ns.model('PaginatedVerificationResponse', {
    'items': fields.List(fields.Nested(verification_record_model)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_pages': fields.Integer(description='总页数'),
    'total_items': fields.Integer(description='总条目数')
})

@ns.route('/submit')
class VerificationSubmissionResource(Resource):
    @jwt_required()
    @ns.expect(verification_submission_input_model, validate=True)
    @ns.response(201, '认证申请提交成功', model=verification_record_model)
    def post(self):
        """用户提交认证申请 (个人实名/企业资质)"""
        current_user_id = get_jwt_identity()
        data = request.json
        # Consider using VerificationRecordCreateSchema for validation if it exists
        try:
            record = verification_service.submit_verification(current_user_id, data)
            record_data = VerificationRecordSchema().dump(record)
            return api_success_response(record_data, 201)
        except (InvalidUsageException, NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"提交认证申请时发生意外错误: {str(e)}", status_code=500, error_code=50001)

# 增加根路由以兼容前端请求 - 移除尾部斜杠，确保兼容性
@ns.route('')
class VerificationRootResource(Resource):
    @jwt_required()
    @ns.expect(verification_submission_input_model, validate=True)
    @ns.response(201, '认证申请提交成功', model=verification_record_model)
    def post(self):
        """用户提交认证申请 (个人实名/企业资质) - 根路径版本"""
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"[VerificationAPI] 收到认证提交请求，用户ID: {current_user_id}")
        current_app.logger.debug(f"[VerificationAPI] 请求内容类型: {request.content_type}")
        
        # 支持JSON和表单数据
        if request.is_json:
            data = request.json
            current_app.logger.debug(f"[VerificationAPI] 从JSON获取数据: {json.dumps(data, ensure_ascii=False)}")
        else:
            # 处理表单数据
            current_app.logger.debug(f"[VerificationAPI] 从表单获取数据，字段: {list(request.form.keys())}")
            data = {
                'profile_type': request.form.get('profile_type'),
                'submitted_data': {}
            }
            
            # 个人认证
            if data['profile_type'] in ['freelancer', 'employer_individual']:
                data['submitted_data'] = {
                    'real_name': request.form.get('real_name'),
                    'id_card_number': request.form.get('id_card_number'),
                    'id_card_photo_front_url': request.form.get('id_card_photo_front_url'),
                    'id_card_photo_back_url': request.form.get('id_card_photo_back_url')
                }
            # 企业认证
            elif data['profile_type'] == 'employer_company':
                data['submitted_data'] = {
                    'company_name': request.form.get('company_name'),
                    'business_license_number': request.form.get('business_license_number'),
                    'legal_representative': request.form.get('legal_representative'),
                    'business_license_photo_url': request.form.get('business_license_photo_url')
                }
            
            current_app.logger.debug(f"[VerificationAPI] 处理后的表单数据: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            if not data.get('profile_type'):
                current_app.logger.error("[VerificationAPI] 缺少必要参数: profile_type")
                raise InvalidUsageException("缺少必要参数: profile_type")
                
            if not data.get('submitted_data'):
                current_app.logger.error("[VerificationAPI] 缺少必要参数: submitted_data")
                raise InvalidUsageException("缺少必要参数: submitted_data")
                
            current_app.logger.info(f"[VerificationAPI] 开始提交认证申请，类型: {data.get('profile_type')}")
            record = verification_service.submit_verification(current_user_id, data)
            record_data = VerificationRecordSchema().dump(record)
            current_app.logger.info(f"[VerificationAPI] 认证申请提交成功，记录ID: {record.id}")
            return api_success_response(record_data, 201)
        except (InvalidUsageException, NotFoundException, BusinessException) as e:
            current_app.logger.error(f"[VerificationAPI] 业务错误: {str(e)}")
            raise e
        except Exception as e:
            current_app.logger.error(f"[VerificationAPI] 未预期错误: {str(e)}", exc_info=True)
            raise BusinessException(message=f"提交认证申请时发生意外错误: {str(e)}", status_code=500, error_code=50001)

@ns.route('/me')
class UserVerificationRecordsResource(Resource):
    @jwt_required()
    @ns.expect(verification_list_parser)
    @ns.response(200, '获取用户认证记录成功', model=paginated_verification_model)
    def get(self):
        """用户获取自己的认证记录 (分页)"""
        current_user_id = get_jwt_identity()
        args = verification_list_parser.parse_args()
        try:
            paginated_records = verification_service.get_user_verification_records(
                current_user_id, 
                profile_type=args.get('profile_type'),
                page=args.get('page'), 
                per_page=args.get('per_page')
            )
            items_data = VerificationRecordSchema(many=True).dump(paginated_records.items)
            return api_success_response({
                'items': items_data,
                'page': paginated_records.page,
                'per_page': paginated_records.per_page,
                'total_pages': paginated_records.pages,
                'total_items': paginated_records.total
            })
        except (NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取认证记录时发生意外错误: {str(e)}", status_code=500, error_code=50001)

# 修改my路由别名为不带斜杠，确保前端调用正确匹配
@ns.route('/my')
class UserVerificationMyResource(Resource):
    @jwt_required()
    @ns.expect(verification_list_parser)
    @ns.response(200, '获取用户认证记录成功', model=paginated_verification_model)
    def get(self):
        """用户获取自己的认证记录 (分页) - 别名路径"""
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"[VerificationAPI] 获取用户认证记录，用户ID: {current_user_id}")
        
        args = verification_list_parser.parse_args()
        current_app.logger.debug(f"[VerificationAPI] 查询参数: {args}")
        
        try:
            current_app.logger.debug(f"[VerificationAPI] 开始查询认证记录，筛选条件: {args.get('profile_type') or '全部'}")
            paginated_records = verification_service.get_user_verification_records(
                current_user_id, 
                profile_type=args.get('profile_type'),
                page=args.get('page'), 
                per_page=args.get('per_page')
            )
            
            items_count = len(paginated_records.items)
            current_app.logger.info(f"[VerificationAPI] 查询到 {items_count} 条认证记录")
            
            items_data = VerificationRecordSchema(many=True).dump(paginated_records.items)
            
            result = {
                'items': items_data,
                'page': paginated_records.page,
                'per_page': paginated_records.per_page,
                'total_pages': paginated_records.pages,
                'total_items': paginated_records.total
            }
            current_app.logger.debug(f"[VerificationAPI] 返回分页数据: 第{result['page']}页/共{result['total_pages']}页")
            
            return api_success_response(result)
        except (NotFoundException, BusinessException) as e:
            current_app.logger.error(f"[VerificationAPI] 业务错误: {str(e)}")
            raise e
        except Exception as e:
            current_app.logger.error(f"[VerificationAPI] 未预期错误: {str(e)}", exc_info=True)
            raise BusinessException(message=f"获取认证记录时发生意外错误: {str(e)}", status_code=500, error_code=50001) 