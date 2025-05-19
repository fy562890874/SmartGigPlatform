"""Application Entry Point (for development)"""
import os
from app import create_app

# Get config name from environment or default to 'development'
config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Use Flask's built-in server for development.
    # For production, use a WSGI server like Gunicorn or uWSGI.
    # Debug mode should be enabled only in development.
    # Host '0.0.0.0' makes the server accessible externally (e.g., within a VM or Docker)
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))

