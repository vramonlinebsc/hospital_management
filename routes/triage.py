# routes/triage.py
"""
Triage routes for patient assessment and priority management
"""
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import current_user, login_required
from functools import wraps
from extensions import db
from models.triage import Triage
from models.triage_assessment import TriageAssessment
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from datetime import datetime, date

# Create blueprint
triage_bp = Blueprint('triage', __name__, url_prefix='/triage')

def triage_required(f):
    """Decorator to require triage role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_triage():
            flash('Access denied. Triage privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@triage_bp.route('/dashboard')
@triage_required
def dashboard():
    """Triage dashboard with today's assessments"""
    triage_user = Triage.query.filter_by(user_id=current_user.id).first()
    
    if not triage_user:
        flash('Triage profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Today's assessments
    today = date.today()
    today_assessments = TriageAssessment.query.filter(
        TriageAssessment.triage_user_id == triage_user.id,
        db.func.date(TriageAssessment.created_at) == today
    ).order_by(TriageAssessment.created_at.desc()).all()
    
    # Pending assessments
    pending_assessments = TriageAssessment.query.filter_by(
        status='Pending'
    ).order_by(TriageAssessment.created_at.desc()).limit(10).all()
    
    # Statistics
    total_today = len(today_assessments)
    emergency_count = sum(1 for a in today_assessments if a.priority_level == 'Emergency')
    urgent_count = sum(1 for a in today_assessments if a.priority_level == 'Urgent')
    
    return render_template('triage/dashboard.html',
                         triage_user=triage_user,
                         today_assessments=today_assessments,
                         pending_assessments=pending_assessments,
                         total_today=total_today,
                         emergency_count=emergency_count,
                         urgent_count=urgent_count)

@triage_bp.route('/assess', methods=['GET', 'POST'])
@triage_required
def assess_patient():
    """Create new triage assessment"""
    triage_user = Triage.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        is_registered = request.form.get('is_registered') == 'yes'
        patient_id = None
        
        if is_registered:
            patient_id = request.form.get('patient_id', type=int)
            patient = Patient.query.get(patient_id)
            if not patient:
                flash('Patient not found.', 'danger')
                return redirect(url_for('triage.assess_patient'))
            patient_name = patient.full_name
            patient_contact = patient.contact_number
            patient_age = None
            patient_gender = patient.gender
        else:
            patient_name = request.form.get('patient_name')
            patient_contact = request.form.get('patient_contact')
            patient_age = request.form.get('patient_age', type=int)
            patient_gender = request.form.get('patient_gender')
        
        chief_complaint = request.form.get('chief_complaint')
        vital_signs = request.form.get('vital_signs')
        priority_level = request.form.get('priority_level')
        recommended_specialization = request.form.get('recommended_specialization')
        notes = request.form.get('notes')
        
        assessment = TriageAssessment(
            triage_user_id=triage_user.id,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_contact=patient_contact,
            patient_age=patient_age,
            patient_gender=patient_gender,
            chief_complaint=chief_complaint,
            vital_signs=vital_signs,
            priority_level=priority_level,
            recommended_specialization=recommended_specialization,
            notes=notes,
            status='Pending'
        )
        db.session.add(assessment)
        db.session.commit()
        
        flash(f'Triage assessment created. Priority: {priority_level}', 'success')
        return redirect(url_for('triage.dashboard'))
    
    patients = Patient.query.filter_by(is_deleted=False, is_active=True).all()
    specializations = db.session.query(Doctor.specialization).filter_by(
        is_deleted=False, is_active=True
    ).distinct().all()
    
    return render_template('triage/assess_patient.html',
                         patients=patients,
                         specializations=[s[0] for s in specializations])

@triage_bp.route('/assessments')
@triage_required
def assessments():
    """View all triage assessments"""
    filter_status = request.args.get('status', 'all')
    filter_priority = request.args.get('priority', 'all')
    
    query = TriageAssessment.query
    
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    
    if filter_priority != 'all':
        query = query.filter_by(priority_level=filter_priority)
    
    assessments = query.order_by(TriageAssessment.created_at.desc()).all()
    
    return render_template('triage/assessments.html',
                         assessments=assessments,
                         filter_status=filter_status,
                         filter_priority=filter_priority)

@triage_bp.route('/assign/<int:assessment_id>', methods=['GET', 'POST'])
@triage_required
def assign_doctor(assessment_id):
    """Assign doctor and create appointment"""
    assessment = TriageAssessment.query.get_or_404(assessment_id)
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        appointment_date_str = request.form.get('appointment_date')
        appointment_time_str = request.form.get('appointment_time')
        
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('triage.assign_doctor', assessment_id=assessment_id))
        
        appointment = Appointment(
            patient_id=assessment.patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=assessment.chief_complaint,
            priority=assessment.priority_level,
            triage_assessment_id=assessment.id,
            status='Booked'
        )
        db.session.add(appointment)
        
        assessment.status = 'Assigned'
        assessment.assigned_doctor_id = doctor_id
        assessment.appointment_id = appointment.id
        
        db.session.commit()
        
        flash('Doctor assigned and appointment created successfully!', 'success')
        return redirect(url_for('triage.dashboard'))
    
    if assessment.recommended_specialization:
        doctors = Doctor.query.filter(
            Doctor.specialization.ilike(f'%{assessment.recommended_specialization}%'),
            Doctor.is_deleted == False,
            Doctor.is_active == True
        ).all()
    else:
        doctors = Doctor.query.filter_by(is_deleted=False, is_active=True).all()
    
    return render_template('triage/assign_doctor.html',
                         assessment=assessment,
                         doctors=doctors,
                         today=date.today().isoformat())