# Configuration file for CivicSightAI Flask application
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Database settings - PostgreSQL/PostGIS
    DATABASE_CONFIG = {
        'dbname': os.environ.get('POSTGRES_DB') or 'civicsightai',
        'user': os.environ.get('POSTGRES_USER') or 'postgres',
        'password': os.environ.get('POSTGRES_PASSWORD') or 'your_postgres_password',  # Change this in production
        'host': os.environ.get('POSTGRES_HOST') or 'localhost',
        'port': int(os.environ.get('POSTGRES_PORT') or 5432)
    }
    
    # Legacy SQLite database URL (for migration reference)
    DATABASE_URL = 'complaints.db'
    
    # Geocoding settings
    GEOCODING_USER_AGENT = 'civicsight-ai'
    
    # Map settings
    DEFAULT_MAP_CENTER = [-74.5, 40]  # New York area [longitude, latitude]
    DEFAULT_MAP_ZOOM = 9
    
    # Email configuration (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your_app_password'  # Using App Password
    MAIL_DEFAULT_SENDER = ('CivicSightAI', MAIL_USERNAME)
    
    # Green API configuration (WhatsApp integration)
    GREENAPI_ID_INSTANCE = os.environ.get('GREENAPI_ID_INSTANCE')
    GREENAPI_API_TOKEN = os.environ.get('GREENAPI_API_TOKEN_INSTANCE')
    
    # Notification settings
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() in ['true', 'on', '1']
    ENABLE_SMS_NOTIFICATIONS = os.environ.get('ENABLE_SMS_NOTIFICATIONS', 'false').lower() in ['true', 'on', '1']
    ENABLE_WHATSAPP_NOTIFICATIONS = os.environ.get('ENABLE_WHATSAPP_NOTIFICATIONS', 'false').lower() in ['true', 'on', '1']
    ENABLE_GREENAPI_WHATSAPP = os.environ.get('ENABLE_GREENAPI_WHATSAPP', 'true').lower() in ['true', 'on', '1']

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific settings here

# Default configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
