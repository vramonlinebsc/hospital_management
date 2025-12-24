"""
Database extensions for Hospital Management System
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail  # ADD THIS LINE
from flask_caching import Cache  # ADD THIS LINE

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

mail = Mail()  # ADD THIS LINE
cache = Cache()  # ADD THIS LINE

def init_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # ADD THIS LINE
    cache.init_app(app)  # ADD THIS LINE
    
    # User loader for Flask-Login
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))