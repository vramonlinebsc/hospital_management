
"""
User model for authentication and role management
"""
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """
    User model for authentication
    Roles: admin, doctor, patient
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, doctor, patient
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctor = db.relationship('Doctor', backref='user', uselist=False, lazy=True)
    patient = db.relationship('Patient', backref='user', uselist=False, lazy=True)
    nurse = db.relationship('Nurse', backref='user', uselist=False, lazy=True)
    triage = db.relationship('Triage', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_doctor(self):
        """Check if user is doctor"""
        return self.role == 'doctor'
    
    def is_patient(self):
        """Check if user is patient"""
        return self.role == 'patient'
    
    def is_nurse(self):
        """Check if user is nurse"""
        return self.role == 'nurse'
    
    def is_triage(self):
        """Check if user is triage"""
        return self.role == 'triage'
    
    def __repr__(self):
        return f'<User {self.username} - {self.role}>'
