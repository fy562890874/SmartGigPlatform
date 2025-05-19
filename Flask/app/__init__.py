"""Application Factory"""
from flask import Flask
from .core import config, extensions
from .api.v1 import v1_blueprint  # Import the v1 API blueprint
from .utils.exceptions import BusinessException # Import base business exception
from .utils.helpers import api_error_response # Import error response helper
import logging # For logging unhandled exceptions

def create_app(config_name='default'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Load configuration
    cfg = config.get_config(config_name)
    app.config.from_object(cfg)
    cfg.init_app(app)  # 执行特定配置的初始化

    # Fix trailing slash issue
    app.url_map.strict_slashes = False

    # Initialize extensions
    extensions.init_app(app)

    # Register blueprints
    app.register_blueprint(v1_blueprint)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Global error handlers
    @app.errorhandler(BusinessException)
    def handle_business_exception(error):
        app.logger.info(f"Business exception: {error.message} (Code: {error.error_code})")
        return api_error_response(
            message=error.message,
            error_code=error.error_code,
            status_code=error.status_code,
            errors=getattr(error, 'errors', None)
        )

    @app.errorhandler(422)  # For Marshmallow validation errors if not caught earlier
    @app.errorhandler(400)  # For other bad requests
    def handle_validation_error(error):
        headers = error.data.get("headers", None) if hasattr(error, 'data') else None
        messages = error.data.get("messages", ["Invalid request."]) if hasattr(error, 'data') else ["Invalid request."]
        
        if isinstance(messages, dict):
            error_payload = messages
            error_message = "输入参数校验失败。"
        else:
            error_payload = None
            error_message = " ".join(str(m) for m in messages)

        app.logger.warning(f"Validation/Bad Request error: {error_message} Details: {error_payload}")
        return api_error_response(message=error_message, error_code=40001, status_code=error.code, errors=error_payload)

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return api_error_response(
            message="服务器内部发生未知错误。",
            error_code=50001,
            status_code=500
        )

    # Add a simple route for testing
    @app.route('/ping')
    def ping():
        return 'pong'

    return app
