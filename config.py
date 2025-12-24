
"""
Configuration settings for Hospital Management System
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hms-dev-secret-key-2025'
    
    # Database settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'hospital.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Appointment settings (configurable)
    APPOINTMENT_SLOT_DURATION = 30  # minutes
    WORKING_HOURS_START = 9  # 9 AM
    WORKING_HOURS_END = 17  # 5 PM
    AVAILABLE_DAYS_AHEAD = 7  # Doctor can set availability for next 7 days
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 2525))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Hospital MS <noreply@hospital.com>')
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = True  # This will show more detailed SMTP logs
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Redis Cache settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Pagination settings
    ITEMS_PER_PAGE = 10
    
    # Admin credentials (for initial setup)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    ADMIN_EMAIL = 'admin@hospital.com'
