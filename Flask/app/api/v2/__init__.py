# app/apis/v2/__init__.py
"""API Version 2 Initialization"""
from flask import Blueprint
from flask_restx import Api
from flask_cors import CORS

v2_blueprint = Blueprint('api_v2', __name__, url_prefix='/api/v2')

CORS(
    v2_blueprint,
    origins="http://localhost:3000", # Or your frontend URL
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    supports_credentials=True,
    expose_headers=["Content-Type", "Authorization"]
)

api_v2 = Api(v2_blueprint,
             title='智慧零工平台 API V2',
             version='2.0',
             description='智慧零工平台后端服务 API 第二版 - 新增及完善接口',
             doc='/doc/', # Consider a different doc path for v2, e.g., /v2/doc/
             authorizations={
                 'apikey': {
                     'type': 'apiKey',
                     'in': 'header',
                     'name': 'Authorization',
                     'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
                 }
             })

# Import and add namespaces for V2
# User API v2 (for missing parts of User Management)

# Payment & Wallet Module
from .payment_wallet_api import ns as payment_wallet_ns
api_v2.add_namespace(payment_wallet_ns, path='/financials') # e.g., /financials/wallets, /financials/payments

# Evaluation Module
from .evaluation_api import ns as evaluation_ns
api_v2.add_namespace(evaluation_ns, path='/evaluations')

# Communication Module (Messages & Notifications)
from .communication_api import ns as communication_ns
api_v2.add_namespace(communication_ns, path='/communications') # e.g., /communications/messages, /communications/notifications

# Favorite Module
from .favorite_api import ns as favorite_ns
api_v2.add_namespace(favorite_ns, path='/favorites')

# Dispute & Report Module
from .dispute_report_api import ns as dispute_report_ns
api_v2.add_namespace(dispute_report_ns, path='/issues') # e.g., /issues/disputes, /issues/reports


# Admin APIs (under a sub-path like /admin)
from .admin import admin_api_v2 # This will be an Api instance itself or just add namespaces directly
# Example if admin_api_v2 is an Api instance mounted on a blueprint:
# v2_blueprint.add_blueprint(admin_api_v2.blueprint, url_prefix='/admin')
# Or if admin namespaces are added directly:
from .admin.admin_system_config_api import ns as admin_system_config_ns
api_v2.add_namespace(admin_system_config_ns, path='/admin/system-configs')

from .admin.admin_user_management_api import ns as admin_user_management_ns
api_v2.add_namespace(admin_user_management_ns, path='/admin/users')

from .admin.admin_job_management_api import ns as admin_job_management_ns
api_v2.add_namespace(admin_job_management_ns, path='/admin/jobs')

from .admin.admin_verification_api import ns as admin_verification_ns
api_v2.add_namespace(admin_verification_ns, path='/admin/verifications')

from .admin.admin_finance_api import ns as admin_finance_ns
api_v2.add_namespace(admin_finance_ns, path='/admin/finance') # for withdrawals etc.

from .admin.admin_dispute_report_api import ns as admin_dispute_report_ns
api_v2.add_namespace(admin_dispute_report_ns, path='/admin/issues') # for disputes & reports

# To use this blueprint in your main app.py:
# from app.apis.v2 import v2_blueprint
# app.register_blueprint(v2_blueprint)