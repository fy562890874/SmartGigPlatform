# app/apis/v2/admin/admin_verification_api.py
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
# Import services, schemas, exceptions, helpers

ns = Namespace('admin_verifications_v2', description='[Admin] 认证审核管理')

# Placeholder: Define models
admin_verification_record_model = ns.model('AdminVerificationRecordV2', { # From verification_api.py potentially
    'id': fields.Integer(),
    'user_id': fields.Integer(),
    'profile_type': fields.String(),
    'submitted_data': fields.Raw(),
    'status': fields.String(),
    'created_at': fields.DateTime()
})
paginated_admin_verifications_model = ns.model('PaginatedAdminVerificationsV2', {
    'items': fields.List(fields.Nested(admin_verification_record_model)),
    # ... pagination fields
})
verification_review_input_model = ns.model('VerificationReviewInputV2', {
    'action': fields.String(required=True, enum=['approve', 'reject']),
    'rejection_reason': fields.String()
})

@ns.route('/pending') # Mapped to /admin/verifications/pending
class AdminVerificationsPendingResource(Resource):
    @jwt_required() # + Admin role check
    @ns.response(200, 'Success', model=paginated_admin_verifications_model)
    @ns.doc(description="12.4. 获取待审核认证 (Admin)")
    def get(self):
        return {"message": "API 12.4 GET /admin/verifications/pending - Placeholder"}, 200

@ns.route('/<int:verification_id>/review')
@ns.param('verification_id', '认证记录ID')
class AdminVerificationReviewResource(Resource):
    @jwt_required() # + Admin role check
    @ns.expect(verification_review_input_model)
    @ns.response(200, 'Success', model=admin_verification_record_model)
    @ns.doc(description="12.4. 管理认证审核 (Admin approve/reject)")
    def put(self, verification_id):
        return {"message": f"API 12.4 PUT /admin/verifications/{verification_id}/review - Placeholder"}, 200