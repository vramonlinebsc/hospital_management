
"""
Database models for Hospital Management System
"""
from flask_login import UserMixin
from datetime import datetime
from extensions import db

# Import all models
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment
from models.doctor_availability import DoctorAvailability
from models.nurse import Nurse
from models.triage import Triage
from models.triage_assessment import TriageAssessment
