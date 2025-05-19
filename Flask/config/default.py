import os

class Config:
    # ... existing config ...

    # Database Configuration
    # Ensure you have pymysql installed: pip install pymysql
    # Format: mysql+pymysql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:root@localhost:3306/smart_gig_platform?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True # Set to True for debugging SQL queries

    # API Configuration
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:5000')

    # ... other config ...
