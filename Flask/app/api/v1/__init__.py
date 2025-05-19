"""API Version 1 Initialization"""
# This file can be used to group namespaces or perform v1 specific setup

# Import namespaces to make them available for the main __init__.py
# from .users import ns as users_ns # This was a placeholder, user_api.py is new
# from .works import ns as works_ns
# from .orders import ns as orders_ns

from flask import Blueprint
from flask_restx import Api
from flask_cors import CORS

# 创建 v1 版本的蓝图, 明确设置 strict_slashes=False
v1_blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Initialize CORS for the v1_blueprint
# This allows requests from 'http://localhost:3000' and handles preflight (OPTIONS) requests.
CORS(
    v1_blueprint,
    origins="http://localhost:3000",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    supports_credentials=True,
    expose_headers=["Content-Type", "Authorization"]
)

# 初始化该蓝图下的 Api 对象
# 注意：这里的 title, version, description 可以根据您的项目进行修改
# API规范文档.md 中提到使用 Flask-RESTX 自动生成 Swagger/OpenAPI 3.0 文档，这些信息会显示在文档中
api_v1 = Api(v1_blueprint,
             title='智慧零工平台 API V1',
             version='1.0',
             description='智慧零工平台后端服务 API 第一版',
             doc='/doc/',
             authorizations={
                 'apikey': {
                     'type': 'apiKey',
                     'in': 'header',
                     'name': 'Authorization',
                     'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
                 }
             })

# 导入具体的 API 模块 (namespaces)
from .auth_api import ns as auth_ns
from .user_api import ns as user_ns # Import the new user_api namespace
from .job_api import ns as job_ns # Import job_ns
from .freelancer_profile_api import ns as freelancer_profile_ns # New
from .employer_profile_api import ns as employer_profile_ns # New
from .job_application_api import ns as job_application_ns # New
from .verification_api import ns as verification_ns # New
from .skill_api import ns as skill_ns # New: Import skill_ns
from .order_api import ns as order_ns # New: Import order_ns

# 将 namespace 添加到 Api 对象
api_v1.add_namespace(auth_ns, path='/auth')
api_v1.add_namespace(user_ns, path='/users') # Register user_ns
api_v1.add_namespace(job_ns, path='/jobs') # Register job_ns
api_v1.add_namespace(freelancer_profile_ns, path='/profiles/freelancer') # New
api_v1.add_namespace(employer_profile_ns, path='/profiles/employer') # New
api_v1.add_namespace(job_application_ns, path='/job-applications') # Corrected path
api_v1.add_namespace(verification_ns, path='/verifications') # New
api_v1.add_namespace(skill_ns, path='/skills') # New: Register skill_ns at /skills path
api_v1.add_namespace(order_ns, path='/orders') # New: Register order_ns

# 您可以在这里添加其他的 namespace
# e.g., for jobs, orders, etc.
