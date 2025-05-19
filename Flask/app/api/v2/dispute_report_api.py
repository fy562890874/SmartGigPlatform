# app/apis/v2/dispute_report_api.py
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from flask import request
# Import services, schemas, exceptions, helpers

ns = Namespace('issues', description='争议与举报模块') # Grouped under 'issues'

# Placeholder: Define models
# --- Dispute Models ---
dispute_input_model = ns.model('DisputeInputV2', {
    'reason': fields.String(required=True),
    'expected_resolution': fields.String(),
    'attachments': fields.List(fields.String(format='url'))
})
dispute_output_model = ns.model('DisputeOutputV2', {
    'id': fields.Integer(),
    'order_id': fields.Integer(),
    'status': fields.String(),
    'reason': fields.String(),
    # ...
})
dispute_update_input_model = ns.model('DisputeUpdateInputV2', {
    'comment': fields.String(), # Example for adding a comment
    'new_attachment_url': fields.String(format='url')
})

# --- Report Models ---
report_input_model = ns.model('ReportInputV2', {
    'report_type': fields.String(required=True, enum=['job', 'user', 'order', 'message', 'evaluation']),
    'target_id': fields.Integer(required=True),
    'reason_category': fields.String(required=True),
    'reason_description': fields.String(),
    'attachments': fields.List(fields.String(format='url'))
})
report_output_model = ns.model('ReportOutputV2', {
    'id': fields.Integer(),
    'reporter_user_id': fields.Integer(),
    'report_type': fields.String(),
    'target_id': fields.Integer(),
    'status': fields.String(),
    # ...
})
paginated_reports_model = ns.model('PaginatedReportsV2', {
    'items': fields.List(fields.Nested(report_output_model)),
    # ... pagination fields
})


@ns.route('/orders/<int:order_id>/disputes')
@ns.param('order_id', '订单ID')
class OrderDisputesResource(Resource):
    @jwt_required()
    @ns.expect(dispute_input_model)
    @ns.response(201, 'Success', model=dispute_output_model)
    @ns.doc(description="10.1. 发起订单争议")
    def post(self, order_id):
        return {"message": f"API 10.1 POST /orders/{order_id}/disputes - Placeholder"}, 201

    @jwt_required() # Or Admin
    @ns.response(200, 'Success', model=dispute_output_model) # Should be single dispute, not list
    @ns.doc(description="10.2. 获取订单的争议信息")
    def get(self, order_id): # There's usually one dispute per order based on your DB schema (unique order_id)
        return {"message": f"API 10.2 GET /orders/{order_id}/dispute - Placeholder"}, 200

@ns.route('/disputes/<int:dispute_id>/actions') # Generic endpoint for updates
@ns.param('dispute_id', '争议ID')
class DisputeActionsResource(Resource):
    @jwt_required() # Or Admin
    @ns.expect(dispute_update_input_model) # This model needs to be more generic or have specific endpoints
    @ns.response(200, 'Success', model=dispute_output_model)
    @ns.doc(description="10.3. 更新争议信息/添加证据")
    def put(self, dispute_id): # Changed to PUT for updates
        return {"message": f"API 10.3 PUT /disputes/{dispute_id}/actions - Placeholder"}, 200

@ns.route('/reports') # Mapped to POST /issues/reports
class ReportListResource(Resource):
    @jwt_required()
    @ns.expect(report_input_model)
    @ns.response(201, 'Success', model=report_output_model)
    @ns.doc(description="10.4. 提交举报")
    def post(self):
        return {"message": "API 10.4 POST /reports - Placeholder"}, 201

@ns.route('/reports/me')
class UserReportsResource(Resource):
    @jwt_required()
    @ns.response(200, 'Success', model=paginated_reports_model)
    @ns.doc(description="10.5. 获取我的举报记录")
    def get(self):
        return {"message": "API 10.5 GET /reports/me - Placeholder"}, 200