# models/triage_assessment.py
"""
Triage Assessment model for patient intake and priority classification
"""
from extensions import db
from datetime import datetime

class TriageAssessment(db.Model):
    """Triage assessment for incoming patients"""
    __tablename__ = 'triage_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    triage_user_id = db.Column(db.Integer, db.ForeignKey('triages.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    
    # Patient details (for walk-ins without accounts)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_contact = db.Column(db.String(20))
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(10))
    
    # Assessment details
    chief_complaint = db.Column(db.Text, nullable=False)
    vital_signs = db.Column(db.Text)
    priority_level = db.Column(db.String(20), nullable=False)
    recommended_specialization = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Status tracking
    status = db.Column(db.String(20), default='Pending', nullable=False)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    triage_user = db.relationship('Triage', backref='assessments', lazy=True)
    patient = db.relationship('Patient', backref='triage_assessments', lazy=True)
    assigned_doctor = db.relationship('Doctor', backref='triage_assignments', lazy=True)
    appointment = db.relationship('Appointment', foreign_keys='Appointment.triage_assessment_id', backref='triage_assessment', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<TriageAssessment {self.id} - {self.priority_level}>'