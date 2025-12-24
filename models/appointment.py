# models/appointment.py
"""
Appointment model for doctor-patient meetings
"""
from extensions import db
from datetime import datetime

class Appointment(db.Model):
    """Appointment booking model"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=True, index=True)
    
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Booked', nullable=False)  # Booked, Completed, Canceled
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    priority = db.Column(db.String(20), default='Standard')
    triage_assessment_id = db.Column(db.Integer, db.ForeignKey('triage_assessments.id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    nurse = db.relationship('Nurse', backref='appointments', lazy=True)
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.status}>'