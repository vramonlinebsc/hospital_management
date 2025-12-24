
"""
Treatment model for medical records
"""
from extensions import db
from datetime import datetime

class Treatment(db.Model):
    """Treatment/Medical record model"""
    __tablename__ = 'treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    test_recommended = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Treatment for Appointment {self.appointment_id}>'
