"""
Doctor routes for appointment management and patient treatment
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from extensions import db
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment
from models.doctor_availability import DoctorAvailability
from utils.decorators import doctor_required
from routes import doctor_bp
from datetime import datetime, date, time, timedelta

@doctor_bp.route('/dashboard')
@doctor_required
def dashboard():
    """Doctor dashboard with appointments"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    today = date.today()
    
    # Today's appointments
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today,
        is_deleted=False
    ).filter(
        Appointment.status.in_(['Booked', 'Completed'])
    ).order_by(Appointment.appointment_time).all()
    
    # This week's appointments
    week_end = today + timedelta(days=7)
    week_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_end,
        Appointment.is_deleted == False,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    # Upcoming appointments (next 10)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.is_deleted == False,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(10).all()
    
    # Assigned patients (unique)
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.is_deleted == False
    ).distinct().all()
    assigned_patients = Patient.query.filter(
        Patient.id.in_([p[0] for p in patient_ids])
    ).all()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         week_appointments=week_appointments,
                         upcoming_appointments=upcoming_appointments,
                         assigned_patients=assigned_patients)

@doctor_bp.route('/appointments')
@doctor_required
def appointments():
    """View all appointments"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'upcoming')
    
    query = Appointment.query.filter_by(doctor_id=doctor.id, is_deleted=False)
    
    if filter_type == 'upcoming':
        query = query.filter(
            Appointment.appointment_date >= date.today(),
            Appointment.status == 'Booked'
        )
    elif filter_type == 'completed':
        query = query.filter(Appointment.status.in_(['Completed', 'Canceled']))
    elif filter_type == 'today':
        query = query.filter(Appointment.appointment_date == date.today())
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('doctor/appointments.html', 
                         appointments=appointments, 
                         filter_type=filter_type,
                         today=date.today())

@doctor_bp.route('/appointments/complete/<int:appointment_id>', methods=['GET', 'POST'])
@doctor_required
def complete_appointment(appointment_id):
    """Mark appointment as completed and add treatment"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify this appointment belongs to the logged-in doctor
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to access this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    if request.method == 'POST':
        
        nurse_id = request.form.get('nurse_id')
        if nurse_id:
            appointment.nurse_id = int(nurse_id) if nurse_id else None
            
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        test_recommended = request.form.get('test_recommended')
        notes = request.form.get('notes')
        follow_up_required = request.form.get('follow_up_required') == 'on'
        follow_up_date_str = request.form.get('follow_up_date')
        
        # Parse follow-up date
        follow_up_date = None
        if follow_up_required and follow_up_date_str:
            try:
                follow_up_date = datetime.strptime(follow_up_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create or update treatment record
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
        if treatment:
            treatment.diagnosis = diagnosis
            treatment.prescription = prescription
            treatment.test_recommended = test_recommended
            treatment.notes = notes
            treatment.follow_up_required = follow_up_required
            treatment.follow_up_date = follow_up_date
        else:
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=diagnosis,
                prescription=prescription,
                test_recommended=test_recommended,
                notes=notes,
                follow_up_required=follow_up_required,
                follow_up_date=follow_up_date
            )
            db.session.add(treatment)
        
        # Update appointment status
        appointment.status = 'Completed'
        db.session.commit()
        
        # Trigger async email task to send treatment summary
        try:
            from tasks import send_treatment_summary
            send_treatment_summary.delay(appointment.id)
        except Exception as e:
            print(f"Warning: Could not queue treatment email: {str(e)}")
        # Don't fail the appointment completion if email fails
        
        
        flash('Appointment completed and treatment recorded.', 'success')
        return redirect(url_for('doctor.appointments'))
    
    # Check if treatment already exists
    existing_treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    from models.nurse import Nurse
    busy_appts = Appointment.query.filter(
        Appointment.id != appointment.id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.appointment_time == appointment.appointment_time,
        Appointment.is_deleted == False,
        Appointment.nurse_id != None
    ).all()
    busy_nurse_ids = [a.nurse_id for a in busy_appts if a.nurse_id]

    if busy_nurse_ids:
        available_nurses = Nurse.query.filter(Nurse.is_active == True, ~Nurse.id.in_(busy_nurse_ids)).all()
        busy_nurses = Nurse.query.filter(Nurse.id.in_(busy_nurse_ids)).all()
    else:
        available_nurses = Nurse.query.filter(Nurse.is_active == True).all()
        busy_nurses = []
    # NEW: Fetch doctor's availability for follow-up scheduling
    from models.doctor_availability import DoctorAvailability
    from datetime import timedelta

    today = date.today()
    future_date = today + timedelta(days=30)  # Show next 30 days

    doctor_availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= future_date,
        DoctorAvailability.is_available == True
    ).all()

    # Get existing appointments for this doctor (to show as blocked)
    doctor_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= future_date,
        Appointment.is_deleted == False,
        Appointment.status.in_(['Booked', 'Completed'])
    ).all()

    return render_template('doctor/complete_appointment.html', 
                         appointment=appointment,
                         treatment=existing_treatment,
                         available_nurses=available_nurses,
                         busy_nurses=busy_nurses,
                         busy_nurse_ids=busy_nurse_ids,
                         doctor_availability=doctor_availability,
                         doctor_appointments=doctor_appointments)

@doctor_bp.route('/appointments/cancel/<int:appointment_id>', methods=['POST'])
@doctor_required
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    appointment.status = 'Canceled'
    db.session.commit()
    
    flash('Appointment has been canceled.', 'success')
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/patients')
@doctor_required
def patients():
    """View all assigned patients"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Get unique patients who have appointments with this doctor
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.is_deleted == False
    ).distinct().all()
    
    patients = Patient.query.filter(
        Patient.id.in_([p[0] for p in patient_ids])
    ).all()
    
    return render_template('doctor/patients.html', patients=patients)

@doctor_bp.route('/patients/history/<int:patient_id>')
@doctor_required
def patient_history(patient_id):
    """View patient's medical history"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all appointments with this doctor
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id,
        is_deleted=False
    ).order_by(Appointment.appointment_date.desc()).all()
    
    # Get all completed appointments with treatments
    treatments = []
    for appointment in appointments:
        if appointment.status == 'Completed' and appointment.treatment:
            treatments.append({
                'appointment': appointment,
                'treatment': appointment.treatment
            })
    
    return render_template('doctor/patient_history.html', 
                         patient=patient, 
                         appointments=appointments,
                         treatments=treatments)

@doctor_bp.route('/availability', methods=['GET', 'POST'])
@doctor_required
def availability():
    """Set availability for next 7 days"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Clear existing availability for next 7 days
        today = date.today()
        future_date = today + timedelta(days=7)
        
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.available_date >= today,
            DoctorAvailability.available_date <= future_date
        ).delete()
        
        # Add new availability
        for i in range(7):
            current_date = today + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            is_available = request.form.get(f'available_{date_str}') == 'on'
            
            if is_available:
                start_time_str = request.form.get(f'start_time_{date_str}')
                end_time_str = request.form.get(f'end_time_{date_str}')
                
                if start_time_str and end_time_str:
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    
                    availability = DoctorAvailability(
                        doctor_id=doctor.id,
                        available_date=current_date,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
                    db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('doctor.availability'))
    
    # Get current availability for next 7 days
    today = date.today()
    availability_data = []
    
    for i in range(7):
        current_date = today + timedelta(days=i)
        availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            available_date=current_date
        ).first()
        
        availability_data.append({
            'date': current_date,
            'availability': availability
        })
    
    return render_template('doctor/availability.html', 
                         availability_data=availability_data)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@doctor_required
def profile():
    """View and edit doctor profile"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        # Update fields from the submitted form (keep existing values if empty)
        doctor.full_name = request.form.get('full_name', doctor.full_name)
        doctor.specialization = request.form.get('specialization', doctor.specialization)
        doctor.qualification = request.form.get('qualification', doctor.qualification)
        experience_years = request.form.get('experience_years')
        if experience_years:
            try:
                doctor.experience_years = int(experience_years)
            except ValueError:
                pass
        doctor.contact_number = request.form.get('contact_number', doctor.contact_number)
        consultation_fee = request.form.get('consultation_fee')
        if consultation_fee:
            try:
                doctor.consultation_fee = float(consultation_fee)
            except ValueError:
                pass
        doctor.bio = request.form.get('bio', doctor.bio)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))

    return render_template('doctor/profile.html', doctor=doctor)