"""Flask Extension Instantiations"""

# Import necessary extension classes
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_cors import CORS  # 添加 CORS 支持
# from flask_socketio import SocketIO # If using SocketIO
# from celery import Celery # Celery setup might be more complex

# Instantiate extensions
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
jwt = JWTManager()
bcrypt = Bcrypt()
cache = Cache()
cors = CORS()  # 实例化 CORS
# socketio = SocketIO() # If using SocketIO

# Celery requires a bit more setup, often done in the app factory or a dedicated file
# def make_celery(app):
#     celery = Celery(
#         app.import_name,
#         backend=app.config['CELERY_RESULT_BACKEND'],
#         broker=app.config['CELERY_BROKER_URL']
#     )
#     celery.conf.update(app.config)
#
#     class ContextTask(celery.Task):
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return self.run(*args, **kwargs)
#
#     celery.Task = ContextTask
#     return celery
#
# celery = None # Placeholder, will be initialized in create_app

def init_app(app):
    """Initialize extensions with the Flask app instance."""
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    
    # 配置 CORS，允许前端跨域请求访问 API
    cors.init_app(
        app, 
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"]
    )
    
    # Initialize Celery if used
    # global celery
    # celery = make_celery(app)

    # JWT配置和回调函数
    from ..services.user_service import user_service
    from flask import jsonify
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from ..models.user import User
        identity = jwt_data["sub"]
        try:
            # 尝试通过UUID查找用户
            return user_service.get_user_by_uuid(identity)
        except:
            try:
                # 尝试通过ID查找用户
                return user_service.get_user_by_id(identity)
            except:
                # 如果找不到用户，返回None
                return None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify(code=401, message='Token has expired', data=None), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify(code=401, message='Invalid token', data=None), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify(code=401, message='Missing JWT token', data=None), 401

