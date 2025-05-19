from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

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