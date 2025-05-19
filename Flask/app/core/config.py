"""Configuration Loading"""
import os
from datetime import timedelta # Ensure timedelta is imported if used

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_secret_key_you_should_change')
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost:3306/smart_gig_platform')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False # Set to True for debugging SQL queries

    # 数据库连接池设置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,             # 连接池大小
        'max_overflow': 20,          # 允许溢出的连接数
        'pool_timeout': 30,          # 等待连接的超时时间（秒）
        'pool_recycle': 1800,        # 连接回收时间（秒），防止MySQL默认8小时断开
        'pool_pre_ping': True        # 使用ping来检查连接是否可用
    }

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'another_secret_key_for_jwt')
    # Configure JWT options like token expiration, etc.
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Redis Configuration (Example)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Celery Configuration (Example)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

    # Flask-Caching Configuration (Example)
    CACHE_TYPE = 'RedisCache' # Or 'SimpleCache' for development
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300 # Default cache timeout in seconds

    # Add other common configurations here
    ITEMS_PER_PAGE = 20

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:root@localhost:3306/smart_gig_platform' # Corrected development DB details
    SQLALCHEMY_ECHO = True # Often useful in development
    # Use simple cache for dev if Redis isn't running
    # CACHE_TYPE = 'SimpleCache'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost/smartgig_test' # Use a separate test DB
    WTF_CSRF_ENABLED = False # Disable CSRF forms validation during tests
    # Use simple cache or mock Redis for tests
    CACHE_TYPE = 'NullCache' # Disable caching for tests

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@prod_db_host/smartgig_prod' # Use production DB details from env vars
    # Ensure SECRET_KEY and JWT_SECRET_KEY are set securely via environment variables in production

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Add production specific initializations, e.g., logging setup
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/smartgig.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('SmartGig Platform startup')


# Dictionary to access configuration classes by name
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig # Default to development
}

def get_config(config_name=None):
    """Gets the configuration object based on name or FLASK_CONFIG env var."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config[config_name]() # Return an instance
