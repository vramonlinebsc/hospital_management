"""
Admin routes for hospital management
Includes dashboard, doctor/patient CRUD, appointments management, and search
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from extensions import db, cache
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment
from utils.decorators import admin_required
from routes import admin_bp
from datetime import datetime, date, timedelta
from sqlalchemy import or_, func
from models.nurse import Nurse
from models.triage import Triage
from sqlalchemy.exc import IntegrityError

@admin_bp.route('/dashboard')
@admin_required
@cache.cached(timeout=300, key_prefix='admin_dashboard')  # ADD THIS LINE - Cache for 5 minutes
def dashboard():
    """Admin dashboard with statistics and charts"""
    # Statistics
    total_doctors = Doctor.query.filter_by(is_deleted=False, is_active=True).count()
    total_patients = Patient.query.filter_by(is_deleted=False, is_active=True).count()
    total_appointments = Appointment.query.filter_by(is_deleted=False).count()
    
    # Today's appointments
    today = date.today()
    today_appointments = Appointment.query.filter_by(
        appointment_date=today,
        is_deleted=False
    ).count()
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= today,
        Appointment.is_deleted == False,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(10).all()
    
    # Recent patients
    recent_patients = Patient.query.filter_by(is_deleted=False).order_by(
        Patient.created_at.desc()
    ).limit(5).all()
    
    # Get appointment statistics for charts
    # Appointments by status
    status_stats = db.session.query(
        Appointment.status,
        func.count(Appointment.id)
    ).filter_by(is_deleted=False).group_by(Appointment.status).all()
    
    # Appointments by doctor (top 5)
    doctor_stats = db.session.query(
        Doctor.full_name,
        func.count(Appointment.id)
    ).join(Appointment).filter(
        Appointment.is_deleted == False
    ).group_by(Doctor.id).order_by(
        func.count(Appointment.id).desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         recent_patients=recent_patients,
                         status_stats=status_stats,
                         doctor_stats=doctor_stats)

# ============= DOCTOR MANAGEMENT =============

@admin_bp.route('/doctors')
@admin_required
def doctors():
    """List all doctors with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    doctors = Doctor.query.filter_by(is_deleted=False).order_by(
        Doctor.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/doctors.html', doctors=doctors)

@admin_bp.route('/doctors/add', methods=['GET', 'POST'])
@admin_required
def add_doctor():
    """Add new doctor"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        specialization = request.form.get('specialization')
        qualification = request.form.get('qualification')
        experience_years = request.form.get('experience_years', type=int)
        contact_number = request.form.get('contact_number')
        license_number = request.form.get('license_number')
        consultation_fee = request.form.get('consultation_fee', type=float)
        bio = request.form.get('bio')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_doctor'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.add_doctor'))
        
        if license_number and Doctor.query.filter_by(license_number=license_number).first():
            flash('License number already exists.', 'danger')
            return redirect(url_for('admin.add_doctor'))
        
        # Create user account
        user = User(username=username, email=email, role='doctor')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            full_name=full_name,
            specialization=specialization,
            qualification=qualification,
            experience_years=experience_years,
            contact_number=contact_number,
            license_number=license_number,
            consultation_fee=consultation_fee or 0.0,
            bio=bio
        )
        db.session.add(doctor)
        db.session.commit()
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/add_doctor.html')

@admin_bp.route('/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
@admin_required
def edit_doctor(doctor_id):
    """Edit doctor details"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        doctor.full_name = request.form.get('full_name')
        doctor.specialization = request.form.get('specialization')
        doctor.qualification = request.form.get('qualification')
        doctor.experience_years = request.form.get('experience_years', type=int)
        doctor.contact_number = request.form.get('contact_number')
        doctor.consultation_fee = request.form.get('consultation_fee', type=float)
        doctor.bio = request.form.get('bio')
        doctor.is_active = request.form.get('is_active') == 'on'
        
        # Update email if changed
        new_email = request.form.get('email')
        if new_email != doctor.user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != doctor.user_id:
                flash('Email already in use.', 'danger')
                return redirect(url_for('admin.edit_doctor', doctor_id=doctor_id))
            doctor.user.email = new_email
        
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/edit_doctor.html', doctor=doctor)

@admin_bp.route('/doctors/delete/<int:doctor_id>', methods=['POST'])
@admin_required
def delete_doctor(doctor_id):
    """Soft delete doctor (blacklist)"""
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_deleted = True
    doctor.is_active = False
    doctor.user.is_active = False
    db.session.commit()
    
    flash('Doctor has been removed/blacklisted.', 'success')
    return redirect(url_for('admin.doctors'))

# ============= PATIENT MANAGEMENT =============

@admin_bp.route('/patients')
@admin_required
def patients():
    """List all patients with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    patients = Patient.query.filter_by(is_deleted=False).order_by(
        Patient.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/patients.html', patients=patients)

@admin_bp.route('/patients/add', methods=['GET', 'POST'])
@admin_required
def add_patient():
    """Add new patient"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        date_of_birth_str = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        address = request.form.get('address')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_patient'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.add_patient'))
        
        # Create user account
        user = User(username=username, email=email, role='patient')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Parse date of birth
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            full_name=full_name,
            contact_number=contact_number,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            address=address
        )
        db.session.add(patient)
        db.session.commit()
        
        flash('Patient added successfully!', 'success')
        return redirect(url_for('admin.patients'))
    
    return render_template('admin/add_patient.html')

@admin_bp.route('/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
@admin_required
def edit_patient(patient_id):
    """Edit patient details"""
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        patient.full_name = request.form.get('full_name')
        patient.contact_number = request.form.get('contact_number')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        patient.is_active = request.form.get('is_active') == 'on'
        
        # Parse date of birth
        date_of_birth_str = request.form.get('date_of_birth')
        if date_of_birth_str:
            try:
                patient.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Update email if changed
        new_email = request.form.get('email')
        if new_email != patient.user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != patient.user_id:
                flash('Email already in use.', 'danger')
                return redirect(url_for('admin.edit_patient', patient_id=patient_id))
            patient.user.email = new_email
        
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.patients'))
    
    return render_template('admin/edit_patient.html', patient=patient)

@admin_bp.route('/patients/delete/<int:patient_id>', methods=['POST'])
@admin_required
def delete_patient(patient_id):
    """Soft delete patient (blacklist)"""
    patient = Patient.query.get_or_404(patient_id)
    patient.is_deleted = True
    patient.is_active = False
    patient.user.is_active = False
    db.session.commit()
    
    flash('Patient has been removed/blacklisted.', 'success')
    return redirect(url_for('admin.patients'))

@admin_bp.route('/patients/view/<int:patient_id>')
@admin_required
def view_patient(patient_id):
    """View patient details and history"""
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        is_deleted=False
    ).order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('admin/view_patient.html', patient=patient, appointments=appointments)

# ============= APPOINTMENT MANAGEMENT =============

@admin_bp.route('/appointments')
@admin_required
def appointments():
    """View all appointments with filters"""
    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Appointment.query.filter_by(is_deleted=False)
    
    if filter_type == 'upcoming':
        query = query.filter(
            Appointment.appointment_date >= date.today(),
            Appointment.status == 'Booked'
        )
    elif filter_type == 'past':
        query = query.filter(
            or_(
                Appointment.appointment_date < date.today(),
                Appointment.status.in_(['Completed', 'Canceled'])
            )
        )
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/appointments.html', 
                         appointments=appointments, 
                         filter_type=filter_type,
                         today=date.today())

@admin_bp.route('/appointments/view/<int:appointment_id>', methods=['GET', 'POST'])
@admin_required
def view_appointment(appointment_id):
    """View appointment details and allow admin to assign/unassign a nurse"""
    appointment = Appointment.query.get_or_404(appointment_id)

    if request.method == 'POST':
        # nurse_id may be empty string when unassigning
        nurse_id = request.form.get('nurse_id')
        if not nurse_id:
            # Unassign
            appointment.nurse_id = None
            db.session.commit()
            flash('Nurse unassigned from appointment.', 'success')
            return redirect(url_for('admin.view_appointment', appointment_id=appointment.id))

        nurse_id = int(nurse_id)
        nurse = Nurse.query.get_or_404(nurse_id)

        # Check for conflicting appointment at same date/time
        conflict = Appointment.query.filter(
            Appointment.id != appointment.id,
            Appointment.nurse_id == nurse.id,
            Appointment.appointment_date == appointment.appointment_date,
            Appointment.appointment_time == appointment.appointment_time,
            Appointment.is_deleted == False
        ).first()
        
        if conflict:
            flash(f'DEBUG: conflict found with appointment ID {conflict.id}', 'warning')
        else:
            flash('DEBUG: no conflict found', 'info')
            
        # Check patient-level one-to-one assignment
        
        patient_conflict = None
        if nurse.assigned_patient_id and nurse.assigned_patient_id != appointment.patient_id:
            patient_conflict = nurse.assigned_patient_id

        # Admin can override; show warnings if conflicts exist
        if conflict:
            flash(f'Warning: Nurse {nurse.full_name} is already booked for another appointment (ID {conflict.id}) at this date/time. Proceeding with assignment (admin override).', 'warning')

        if patient_conflict:
            flash(f'Note: Nurse {nurse.full_name} is currently assigned to patient ID {patient_conflict}. Proceeding with assignment (admin override).', 'warning')

        try:
            appointment.nurse_id = nurse.id
            db.session.commit()
            flash(f'Nurse {nurse.full_name} assigned to appointment.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Failed to assign nurse due to database constraint. Please try again.', 'danger')

        return redirect(url_for('admin.view_appointment', appointment_id=appointment.id))

    # GET: prepare nurse lists for the template
    # busy nurse ids at the same date/time (excluding this appointment)
    busy_appts = Appointment.query.filter(
        Appointment.id != appointment.id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.appointment_time == appointment.appointment_time,
        Appointment.is_deleted == False,
        Appointment.nurse_id != None
    ).all()
    busy_nurse_ids = [a.nurse_id for a in busy_appts if a.nurse_id]

    # available nurses: active nurses not in busy list
    if busy_nurse_ids:
        available_nurses = Nurse.query.filter(Nurse.is_active == True, ~Nurse.id.in_(busy_nurse_ids)).all()
        # fetch Nurse objects for busy nurses so template can show names
        busy_nurses = Nurse.query.filter(Nurse.id.in_(busy_nurse_ids)).all()
    else:
        available_nurses = Nurse.query.filter(Nurse.is_active == True).all()
        busy_nurses = []

    # pass assigned nurse and available lists to template
    return render_template('admin/view_appointment.html',
                       appointment=appointment,
                       available_nurses=available_nurses,
                       busy_nurse_ids=busy_nurse_ids,
                       busy_nurses=busy_nurses)

# ============= SEARCH FUNCTIONALITY =============

@admin_bp.route('/search')
@admin_required
def search():
    """Advanced search for doctors and patients"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    doctors = []
    patients = []
    
    if query:
        if search_type in ['all', 'doctors']:
            # Search doctors by name, specialization, license number, contact
            doctors = Doctor.query.filter(
                Doctor.is_deleted == False,
                or_(
                    Doctor.full_name.ilike(f'%{query}%'),
                    Doctor.specialization.ilike(f'%{query}%'),
                    Doctor.license_number.ilike(f'%{query}%'),
                    Doctor.contact_number.ilike(f'%{query}%')
                )
            ).all()
        
        if search_type in ['all', 'patients']:
            # Search patients by name, ID, contact
            patients = Patient.query.filter(
                Patient.is_deleted == False,
                or_(
                    Patient.full_name.ilike(f'%{query}%'),
                    Patient.contact_number.ilike(f'%{query}%'),
                    Patient.id == int(query) if query.isdigit() else False
                )
            ).all()
    
    return render_template('admin/search.html', 
                         doctors=doctors, 
                         patients=patients, 
                         query=query, 
                         search_type=search_type)
    
    
# ============= NURSE MANAGEMENT =============

@admin_bp.route('/nurses')
@admin_required
def nurses():
    """List all nurses with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    nurses = Nurse.query.join(User).filter(
        User.is_active == True
    ).order_by(Nurse.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/nurses.html', nurses=nurses)

@admin_bp.route('/nurses/add', methods=['GET', 'POST'])
@admin_required
def add_nurse():
    """Add new nurse"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        department = request.form.get('department')

        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_nurse'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.add_nurse'))

        # Create user account
        user = User(username=username, email=email, role='nurse')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create nurse profile
        nurse = Nurse(
            user_id=user.id,
            full_name=full_name,
            contact_number=contact_number,
            department=department
        )
        db.session.add(nurse)
        db.session.commit()

        flash('Nurse added successfully!', 'success')
        return redirect(url_for('admin.nurses'))

    return render_template('admin/add_nurse.html')

@admin_bp.route('/nurses/edit/<int:nurse_id>', methods=['GET', 'POST'])
@admin_required
def edit_nurse(nurse_id):
    """Edit nurse details"""
    nurse = Nurse.query.get_or_404(nurse_id)

    if request.method == 'POST':
        nurse.full_name = request.form.get('full_name')
        nurse.contact_number = request.form.get('contact_number')
        nurse.department = request.form.get('department')
        nurse.is_active = request.form.get('is_active') == 'on'

        # Update email if changed
        new_email = request.form.get('email')
        if new_email != nurse.user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != nurse.user_id:
                flash('Email already in use.', 'danger')
                return redirect(url_for('admin.edit_nurse', nurse_id=nurse_id))
            nurse.user.email = new_email

        db.session.commit()
        flash('Nurse updated successfully!', 'success')
        return redirect(url_for('admin.nurses'))

    return render_template('admin/edit_nurse.html', nurse=nurse)

@admin_bp.route('/nurses/delete/<int:nurse_id>', methods=['POST'])
@admin_required
def delete_nurse(nurse_id):
    """Soft delete nurse"""
    nurse = Nurse.query.get_or_404(nurse_id)
    # DEBUG: log what appointments exist for this nurse at this slot
    busy_for_nurse = Appointment.query.filter( 
        Appointment.id != appointment.id,
        Appointment.nurse_id == nurse.id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.appointment_time == appointment.appointment_time,
        Appointment.is_deleted == False
    ).all()
    flash(f'DEBUG: nurse={nurse.id} appt_date={appointment.appointment_date} appt_time={appointment.appointment_time} busy_appt_ids={[a.id for a in busy_for_nurse]}', 'info')
    nurse.is_active = False
    nurse.user.is_active = False
    db.session.commit()

    flash('Nurse has been deactivated.', 'success')
    return redirect(url_for('admin.nurses'))

@admin_bp.route('/nurses/assign-doctor/<int:nurse_id>', methods=['GET', 'POST'])
@admin_required
def assign_doctor_to_nurse(nurse_id):
    """Assign doctors to a nurse"""
    nurse = Nurse.query.get_or_404(nurse_id)
    all_doctors = Doctor.query.filter_by(is_deleted=False, is_active=True).all()

    if request.method == 'POST':
        # Collect selected doctor IDs from form (checkboxes named 'doctor_ids')
        selected = request.form.getlist('doctor_ids')
        # Persist using helper on model (expects list of ids)
        nurse.set_assigned_doctor_ids(selected)
        db.session.commit()

        flash(f'Doctor assignments updated for {nurse.full_name}.', 'success')
        return redirect(url_for('admin.nurses'))

    # Prepare assigned ids for the template (list of ints)
    assigned_ids = nurse.get_assigned_doctor_ids() if nurse else []
    # GET: show form with checkboxes for all active doctors
    return render_template('admin/assign_doctor.html', nurse=nurse, doctors=all_doctors, assigned_ids=assigned_ids)


@admin_bp.route('/api/nurses/<int:nurse_id>/assigned-doctors')
@admin_required
def api_get_assigned_doctors(nurse_id):
    """API: Get list of assigned doctor names for a nurse"""
    nurse = Nurse.query.get_or_404(nurse_id)
    ids = nurse.get_assigned_doctor_ids()
    doctors = Doctor.query.filter(Doctor.id.in_(ids)).all() if ids else []
    names = [{'id': d.id, 'name': d.full_name} for d in doctors]
    return jsonify({'doctors': names})



# ============= TRIAGE MANAGEMENT =============

@admin_bp.route('/triages')
@admin_required
def triages():
    """List all triage users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    triages = Triage.query.join(User).filter(
        User.is_active == True
    ).order_by(Triage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/triages.html', triages=triages)

@admin_bp.route('/triages/add', methods=['GET', 'POST'])
@admin_required
def add_triage():
    """Add new triage user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        department = request.form.get('department')

        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_triage'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.add_triage'))

        # Create user account
        user = User(username=username, email=email, role='triage')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create triage profile
        tri = Triage(
            user_id=user.id,
            full_name=full_name,
            contact_number=contact_number,
            department=department
        )
        db.session.add(tri)
        db.session.commit()

        flash('Triage user added successfully!', 'success')
        return redirect(url_for('admin.triages'))

    return render_template('admin/add_triage.html')

@admin_bp.route('/triages/edit/<int:triage_id>', methods=['GET', 'POST'])
@admin_required
def edit_triage(triage_id):
    """Edit triage details"""
    tri = Triage.query.get_or_404(triage_id)

    if request.method == 'POST':
        tri.full_name = request.form.get('full_name')
        tri.contact_number = request.form.get('contact_number')
        tri.department = request.form.get('department')
        tri.is_active = request.form.get('is_active') == 'on'

        # Update email if changed
        new_email = request.form.get('email')
        if new_email != tri.user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != tri.user_id:
                flash('Email already in use.', 'danger')
                return redirect(url_for('admin.edit_triage', triage_id=triage_id))
            tri.user.email = new_email

        db.session.commit()
        flash('Triage updated successfully!', 'success')
        return redirect(url_for('admin.triages'))

    return render_template('admin/edit_triage.html', triage=tri)

@admin_bp.route('/triages/delete/<int:triage_id>', methods=['POST'])
@admin_required
def delete_triage(triage_id):
    """Soft delete triage"""
    tri = Triage.query.get_or_404(triage_id)
    tri.is_active = False
    tri.user.is_active = False
    db.session.commit()

    flash('Triage user has been deactivated.', 'success')
    return redirect(url_for('admin.triages'))


@admin_bp.route('/appointments/cancel/<int:appointment_id>', methods=['POST'])
@admin_required
def cancel_appointment(appointment_id):
    """Cancel an appointment (admin override)"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.status not in ['Booked']:
        flash('Only booked appointments can be canceled.', 'warning')
        return redirect(url_for('admin.appointments'))
    
    appointment.status = 'Canceled'
    db.session.commit()
    
    flash(f'Appointment #{appointment_id} has been canceled.', 'success')
    return redirect(url_for('admin.appointments'))


@admin_bp.route('/appointments/book', methods=['GET', 'POST'])
@admin_required
def book_appointment():
    """Admin: Book an appointment for any patient with any doctor"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date_str = request.form.get('appointment_date')
        appointment_time_str = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('admin.book_appointment'))
        
        # Validate future date
        if appointment_date < date.today():
            flash('Cannot book appointments in the past.', 'danger')
            return redirect(url_for('admin.book_appointment'))
        
        # Check slot availability
        from utils.helpers import is_slot_available
        is_avail, msg = is_slot_available(doctor_id, appointment_date, appointment_time)
        if not is_avail:
            flash(f'Time slot not available: {msg}', 'danger')
            return redirect(url_for('admin.book_appointment'))
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Booked'
        )
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('admin.appointments'))
    
    # GET: Show form
    from models.patient import Patient
    from models.doctor import Doctor
    
    patients = Patient.query.filter_by(is_deleted=False, is_active=True).all()
    doctors = Doctor.query.filter_by(is_deleted=False, is_active=True).all()
    
    return render_template('admin/book_appointment.html',
                         patients=patients,
                         doctors=doctors)

@admin_bp.route('/appointments/reschedule/<int:appointment_id>', methods=['GET', 'POST'])
@admin_required
def reschedule_appointment(appointment_id):
    """Admin: Reschedule an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'POST':
        new_date_str = request.form.get('appointment_date')
        new_time_str = request.form.get('appointment_time')
        
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            new_time = datetime.strptime(new_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('admin.reschedule_appointment', appointment_id=appointment_id))
        
        # Validate future date
        if new_date < date.today():
            flash('Cannot reschedule to a past date.', 'danger')
            return redirect(url_for('admin.reschedule_appointment', appointment_id=appointment_id))
        
        # Check if new slot is available
        from utils.helpers import is_slot_available
        is_avail, msg = is_slot_available(appointment.doctor_id, new_date, new_time, exclude_appointment_id=appointment_id)
        if not is_avail:
            flash(f'Time slot not available: {msg}', 'danger')
            return redirect(url_for('admin.reschedule_appointment', appointment_id=appointment_id))
        
        # Update appointment
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        db.session.commit()
        
        flash('Appointment rescheduled successfully!', 'success')
        return redirect(url_for('admin.appointments'))
    
    # GET: Show reschedule form
    return render_template('admin/reschedule_appointment.html',
                         appointment=appointment)
    

# ============= ACTIVATE/DEACTIVATE ROUTES =============

@admin_bp.route('/doctors/toggle-status/<int:doctor_id>', methods=['POST'])
@admin_required
def toggle_doctor_status(doctor_id):
    """Toggle doctor active/inactive status"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Toggle status
    doctor.is_active = not doctor.is_active
    doctor.user.is_active = doctor.is_active
    db.session.commit()
    
    status = "activated" if doctor.is_active else "deactivated"
    flash(f'Doctor {doctor.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.doctors'))

@admin_bp.route('/patients/toggle-status/<int:patient_id>', methods=['POST'])
@admin_required
def toggle_patient_status(patient_id):
    """Toggle patient active/inactive status"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Toggle status
    patient.is_active = not patient.is_active
    patient.user.is_active = patient.is_active
    db.session.commit()
    
    status = "activated" if patient.is_active else "deactivated"
    flash(f'Patient {patient.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.patients'))

@admin_bp.route('/nurses/toggle-status/<int:nurse_id>', methods=['POST'])
@admin_required
def toggle_nurse_status(nurse_id):
    """Toggle nurse active/inactive status"""
    nurse = Nurse.query.get_or_404(nurse_id)
    
    # Toggle status
    nurse.is_active = not nurse.is_active
    nurse.user.is_active = nurse.is_active
    db.session.commit()
    
    status = "activated" if nurse.is_active else "deactivated"
    flash(f'Nurse {nurse.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.nurses'))