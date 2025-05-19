"""API Version 1 Initialization"""
# This file can be used to group namespaces or perform v1 specific setup

# Import namespaces to make them available for the main __init__.py
# from .users import ns as users_ns # This was a placeholder, user_api.py is new
# from .works import ns as works_ns
# from .orders import ns as orders_ns

from flask import Blueprint
from flask_restx import Api
from flask_cors import CORS

# 创建Blueprint
v1_blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 应用CORS到blueprint
CORS(v1_blueprint, resources={r"/*": {"origins": "*"}})

# 创建API实例
api = Api(
    v1_blueprint,
    version='1.0',
    title='智慧零工平台 API',
    description='智慧零工平台后端API服务',
    doc='/docs'
)

# 导入所有命名空间
from .user_api import ns as user_ns
from .auth_api import ns as auth_ns
from .job_api import ns as job_ns
from .skill_api import ns as skill_ns
from .job_application_api import ns as job_application_ns
from .order_api import ns as order_ns
from .verification_api import ns as verification_ns
from .freelancer_profile_api import ns as freelancer_profile_ns
from .employer_profile_api import ns as employer_profile_ns
# from .admin_api import ns as admin_ns  # 可选，如果有管理员API

# 添加命名空间到API
api.add_namespace(user_ns)
api.add_namespace(auth_ns)
api.add_namespace(job_ns)
api.add_namespace(skill_ns)
api.add_namespace(job_application_ns)
api.add_namespace(order_ns)
api.add_namespace(verification_ns)
api.add_namespace(freelancer_profile_ns)
api.add_namespace(employer_profile_ns)
# api.add_namespace(admin_ns)  # 可选，如果有管理员API

# 您可以在这里添加其他的 namespace
# e.g., for jobs, orders, etc.
