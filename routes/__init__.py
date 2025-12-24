
"""
Routes initialization for Hospital Management System
"""
from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')
patient_bp = Blueprint('patient', __name__, url_prefix='/patient')
api_bp = Blueprint('api', __name__, url_prefix='/api')
main_bp = Blueprint('main', __name__)

# Import routes

from routes import auth, admin, doctor, patient, api, main, triage


# Import the triage blueprint from the triage module
from routes.triage import triage_bp