"""
REST API endpoints for Hospital Management System
Provides JSON responses for CRUD operations

Endpoints:
- GET /api/doctors - List all doctors
- GET /api/doctors/<id> - Get doctor details
- POST /api/doctors - Create doctor (admin only)
- PUT /api/doctors/<id> - Update doctor (admin only)
- DELETE /api/doctors/<id> - Delete doctor (admin only)

- GET /api/patients - List all patients
- GET /api/patients/<id> - Get patient details
- POST /api/patients - Create patient
- PUT /api/patients/<id> - Update patient
- DELETE /api/patients/<id> - Delete patient (admin only)

- GET /api/appointments - List appointments
- GET /api/appointments/<id> - Get appointment details
- POST /api/appointments - Create appointment
- PUT /api/appointments/<id> - Update appointment
- DELETE /api/appointments/<id> - Cancel appointment

- GET /api/stats - Get system statistics (admin only)
"""
from flask import jsonify, request
from flask_login import current_user, login_required
from extensions import db
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.user import User
from routes import api_bp
from datetime import datetime, date

# Helper function to serialize models
def serialize_doctor(doctor):
    """Serialize doctor object to dictionary"""
    return {
        'id': doctor.id,
        'full_name': doctor.full_name,
        'specialization': doctor.specialization,
        'qualification': doctor.qualification,
        'experience_years': doctor.experience_years,
        'contact_number': doctor.contact_number,
        'consultation_fee': doctor.consultation_fee,
        'bio': doctor.bio,
        'is_active': doctor.is_active,
        'email': doctor.user.email
    }

def serialize_patient(patient):
    """Serialize patient object to dictionary"""
    return {
        'id': patient.id,
        'full_name': patient.full_name,
        'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        'gender': patient.gender,
        'blood_group': patient.blood_group,
        'contact_number': patient.contact_number,
        'address': patient.address,
        'email': patient.user.email,
        'is_active': patient.is_active
    }

def serialize_appointment(appointment):
    """Serialize appointment object to dictionary"""
    return {
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'patient_name': appointment.patient.full_name,
        'doctor_id': appointment.doctor_id,
        'doctor_name': appointment.doctor.full_name,
        'appointment_date': appointment.appointment_date.isoformat(),
        'appointment_time': appointment.appointment_time.strftime('%H:%M'),
        'status': appointment.status,
        'reason': appointment.reason,
        'notes': appointment.notes
    }

# ============= DOCTOR ENDPOINTS =============

@api_bp.route('/doctors', methods=['GET'])
def get_doctors():
    """
    GET /api/doctors
    Query parameters:
    - specialization: Filter by specialization
    - active: Filter by active status (true/false)
    """
    specialization = request.args.get('specialization')
    active = request.args.get('active', 'true').lower() == 'true'
    
    query = Doctor.query.filter_by(is_deleted=False)
    
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f'%{specialization}%'))
    
    if active:
        query = query.filter_by(is_active=True)
    
    doctors = query.all()
    
    return jsonify({
        'success': True,
        'count': len(doctors),
        'data': [serialize_doctor(d) for d in doctors]
    }), 200

@api_bp.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """GET /api/doctors/<id> - Get doctor details"""
    doctor = Doctor.query.filter_by(id=doctor_id, is_deleted=False).first()
    
    if not doctor:
        return jsonify({
            'success': False,
            'message': 'Doctor not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': serialize_doctor(doctor)
    }), 200

@api_bp.route('/doctors', methods=['POST'])
@login_required
def create_doctor():
    """POST /api/doctors - Create new doctor (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Unauthorized - Admin access required'
        }), 403
    
    data = request.get_json()
    
    # Validation
    required_fields = ['username', 'email', 'password', 'full_name', 'specialization', 'contact_number']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Check uniqueness
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered'
        }), 400
    
    # Create user
    user = User(username=data['username'], email=data['email'], role='doctor')
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()
    
    # Create doctor
    doctor = Doctor(
        user_id=user.id,
        full_name=data['full_name'],
        specialization=data['specialization'],
        qualification=data.get('qualification'),
        experience_years=data.get('experience_years'),
        contact_number=data['contact_number'],
        license_number=data.get('license_number'),
        consultation_fee=data.get('consultation_fee', 0.0),
        bio=data.get('bio')
    )
    db.session.add(doctor)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Doctor created successfully',
        'data': serialize_doctor(doctor)
    }), 201

@api_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@login_required
def update_doctor(doctor_id):
    """PUT /api/doctors/<id> - Update doctor (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Unauthorized - Admin access required'
        }), 403
    
    doctor = Doctor.query.get_or_404(doctor_id)
    data = request.get_json()
    
    # Update fields
    if 'full_name' in data:
        doctor.full_name = data['full_name']
    if 'specialization' in data:
        doctor.specialization = data['specialization']
    if 'qualification' in data:
        doctor.qualification = data['qualification']
    if 'experience_years' in data:
        doctor.experience_years = data['experience_years']
    if 'contact_number' in data:
        doctor.contact_number = data['contact_number']
    if 'consultation_fee' in data:
        doctor.consultation_fee = data['consultation_fee']
    if 'bio' in data:
        doctor.bio = data['bio']
    if 'is_active' in data:
        doctor.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Doctor updated successfully',
        'data': serialize_doctor(doctor)
    }), 200

@api_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@login_required
def delete_doctor(doctor_id):
    """DELETE /api/doctors/<id> - Delete doctor (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Unauthorized - Admin access required'
        }), 403
    
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_deleted = True
    doctor.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Doctor deleted successfully'
    }), 200

# ============= PATIENT ENDPOINTS =============

@api_bp.route('/patients', methods=['GET'])
@login_required
def get_patients():
    """GET /api/patients - List all patients"""
    patients = Patient.query.filter_by(is_deleted=False).all()
    
    return jsonify({
        'success': True,
        'count': len(patients),
        'data': [serialize_patient(p) for p in patients]
    }), 200

@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
@login_required
def get_patient(patient_id):
    """GET /api/patients/<id> - Get patient details"""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first()
    
    if not patient:
        return jsonify({
            'success': False,
            'message': 'Patient not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': serialize_patient(patient)
    }), 200

@api_bp.route('/patients', methods=['POST'])
def create_patient():
    """POST /api/patients - Create new patient (registration)"""
    data = request.get_json()
    
    # Validation
    required_fields = ['username', 'email', 'password', 'full_name', 'contact_number']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Check uniqueness
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered'
        }), 400
    
    # Create user
    user = User(username=data['username'], email=data['email'], role='patient')
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()
    
    # Parse date of birth
    date_of_birth = None
    if 'date_of_birth' in data:
        try:
            date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Create patient
    patient = Patient(
        user_id=user.id,
        full_name=data['full_name'],
        contact_number=data['contact_number'],
        date_of_birth=date_of_birth,
        gender=data.get('gender'),
        blood_group=data.get('blood_group'),
        address=data.get('address')
    )
    db.session.add(patient)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Patient created successfully',
        'data': serialize_patient(patient)
    }), 201

@api_bp.route('/patients/<int:patient_id>', methods=['PUT'])
@login_required
def update_patient(patient_id):
    """PUT /api/patients/<id> - Update patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Authorization: patients can only update their own profile, admin can update any
    if not current_user.is_admin() and patient.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Unauthorized'
        }), 403
    
    data = request.get_json()
    
    # Update fields
    if 'full_name' in data:
        patient.full_name = data['full_name']
    if 'contact_number' in data:
        patient.contact_number = data['contact_number']
    if 'gender' in data:
        patient.gender = data['gender']
    if 'blood_group' in data:
        patient.blood_group = data['blood_group']
    if 'address' in data:
        patient.address = data['address']
    if 'date_of_birth' in data:
        try:
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Patient updated successfully',
        'data': serialize_patient(patient)
    }), 200

# ============= APPOINTMENT ENDPOINTS =============

@api_bp.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    """
    GET /api/appointments - List appointments
    Query parameters:
    - status: Filter by status (Booked, Completed, Canceled)
    - doctor_id: Filter by doctor
    - patient_id: Filter by patient
    """
    query = Appointment.query.filter_by(is_deleted=False)
    
    status = request.args.get('status')
    doctor_id = request.args.get('doctor_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    
    if status:
        query = query.filter_by(status=status)
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    appointments = query.all()
    
    return jsonify({
        'success': True,
        'count': len(appointments),
        'data': [serialize_appointment(a) for a in appointments]
    }), 200

@api_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment(appointment_id):
    """GET /api/appointments/<id> - Get appointment details"""
    appointment = Appointment.query.filter_by(id=appointment_id, is_deleted=False).first()
    
    if not appointment:
        return jsonify({
            'success': False,
            'message': 'Appointment not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': serialize_appointment(appointment)
    }), 200

@api_bp.route('/appointments', methods=['POST'])
@login_required
def create_appointment():
    """POST /api/appointments - Create new appointment"""
    data = request.get_json()
    
    # Validation
    required_fields = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Parse date and time
    try:
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid date or time format'
        }), 400
    
    # Validate date is not in the past
    if appointment_date < date.today():
        return jsonify({
            'success': False,
            'message': 'Cannot book appointments in the past'
        }), 400
    
    # Check if slot is available
    existing = Appointment.query.filter_by(
        doctor_id=data['doctor_id'],
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        is_deleted=False
    ).filter(Appointment.status != 'Canceled').first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': 'This time slot is not available'
        }), 409
    
    # Create appointment
    appointment = Appointment(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=data.get('reason'),
        status='Booked'
    )
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Appointment created successfully',
        'data': serialize_appointment(appointment)
    }), 201

@api_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    """PUT /api/appointments/<id> - Update appointment status"""
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json()
    
    if 'status' in data:
        if data['status'] in ['Booked', 'Completed', 'Canceled']:
            appointment.status = data['status']
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid status value'
            }), 400
    
    if 'notes' in data:
        appointment.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Appointment updated successfully',
        'data': serialize_appointment(appointment)
    }), 200

@api_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
def cancel_appointment(appointment_id):
    """DELETE /api/appointments/<id> - Cancel appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    appointment.status = 'Canceled'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Appointment canceled successfully'
    }), 200

# ============= STATISTICS ENDPOINT =============

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """GET /api/stats - Get system statistics (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Unauthorized - Admin access required'
        }), 403
    
    stats = {
        'total_doctors': Doctor.query.filter_by(is_deleted=False, is_active=True).count(),
        'total_patients': Patient.query.filter_by(is_deleted=False, is_active=True).count(),
        'total_appointments': Appointment.query.filter_by(is_deleted=False).count(),
        'booked_appointments': Appointment.query.filter_by(is_deleted=False, status='Booked').count(),
        'completed_appointments': Appointment.query.filter_by(is_deleted=False, status='Completed').count(),
        'canceled_appointments': Appointment.query.filter_by(is_deleted=False, status='Canceled').count()
    }
    
    return jsonify({
        'success': True,
        'data': stats
    }), 200
    
@api_bp.route('/doctor/<int:doctor_id>/availability')
def doctor_availability(doctor_id):
    """Get doctor availability and booked appointments"""
    from models.doctor_availability import DoctorAvailability
    from models.appointment import Appointment
    from datetime import date, timedelta
    
    today = date.today()
    future = today + timedelta(days=30)
    
    # Get availability
    avail = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= future,
        DoctorAvailability.is_available == True
    ).all()
    
    # Get booked appointments
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= future,
        Appointment.is_deleted == False,
        Appointment.status == 'Booked'
    ).all()
    
    return jsonify({
        'success': True,
        'availability': [{
            'date': a.available_date.isoformat(),
            'start_time': a.start_time.strftime('%H:%M'),
            'end_time': a.end_time.strftime('%H:%M')
        } for a in avail],
        'appointments': [{
            'date': apt.appointment_date.isoformat(),
            'time': apt.appointment_time.strftime('%H:%M'),
            'end_time': (datetime.combine(date.today(), apt.appointment_time) + timedelta(minutes=30)).strftime('%H:%M')
        } for apt in appointments]
    })
    
    
