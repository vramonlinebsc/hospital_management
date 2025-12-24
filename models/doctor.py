
"""
Doctor model for medical professionals
"""
from extensions import db
from datetime import datetime

class Doctor(db.Model):
    """Doctor profile model"""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False, index=True)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    contact_number = db.Column(db.String(20))
    license_number = db.Column(db.String(50), unique=True)
    consultation_fee = db.Column(db.Float, default=0.0)
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Doctor {self.full_name} - {self.specialization}>'
