"""
Patient routes for booking appointments and viewing history
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from extensions import db, cache
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.treatment import Treatment
from models.doctor_availability import DoctorAvailability
from utils.decorators import patient_required
from utils.helpers import is_slot_available, send_email, generate_time_slots
from routes import patient_bp
from datetime import datetime, date, timedelta
from config import Config

@patient_bp.route('/dashboard')
@patient_required
@cache.cached(timeout=180, key_prefix=lambda: f'patient_dashboard_{current_user.id}')  # ADD THIS LINE - Cache for 3 minutes
def dashboard():
    """Patient dashboard"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all specializations
    specializations = db.session.query(Doctor.specialization).filter_by(
        is_deleted=False,
        is_active=True
    ).distinct().all()
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= date.today(),
        Appointment.is_deleted == False,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(5).all()
    
    # Recent treatments
    recent_treatments = db.session.query(Appointment, Treatment).join(
        Treatment, Appointment.id == Treatment.appointment_id
    ).filter(
        Appointment.patient_id == patient.id,
        Appointment.status == 'Completed'
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    
    return render_template('patient/dashboard.html',
                         patient=patient,
                         specializations=[s[0] for s in specializations],
                         upcoming_appointments=upcoming_appointments,
                         recent_treatments=recent_treatments)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@patient_required
def profile():
    """View and edit patient profile"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        patient.full_name = request.form.get('full_name')
        patient.contact_number = request.form.get('contact_number')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        patient.emergency_contact_name = request.form.get('emergency_contact_name')
        patient.emergency_contact_number = request.form.get('emergency_contact_number')
        patient.medical_history = request.form.get('medical_history')
        patient.allergies = request.form.get('allergies')
        
        # Parse date of birth
        date_of_birth_str = request.form.get('date_of_birth')
        if date_of_birth_str:
            try:
                patient.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    
    return render_template('patient/profile.html', patient=patient)

@patient_bp.route('/doctors')
@patient_required
@cache.cached(timeout=600, query_string=True)  # ADD THIS LINE - Cache for 10 minutes, include query params
def doctors():
    """Search and view available doctors"""
    specialization = request.args.get('specialization', '')
    search_query = request.args.get('q', '')
    
    query = Doctor.query.filter_by(is_deleted=False, is_active=True)
    
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f'%{specialization}%'))
    
    if search_query:
        query = query.filter(Doctor.full_name.ilike(f'%{search_query}%'))
    
    doctors = query.all()
    
    # Get all specializations for filter
    all_specializations = db.session.query(Doctor.specialization).filter_by(
        is_deleted=False,
        is_active=True
    ).distinct().all()
    
    # Get availability for each doctor (next 7 days)
    today = date.today()
    future_date = today + timedelta(days=7)
    
    doctor_availability = {}
    for doctor in doctors:
        available_dates = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.available_date >= today,
            DoctorAvailability.available_date <= future_date,
            DoctorAvailability.is_available == True
        ).all()
        doctor_availability[doctor.id] = available_dates
    
    return render_template('patient/doctors.html',
                         doctors=doctors,
                         specializations=[s[0] for s in all_specializations],
                         selected_specialization=specialization,
                         search_query=search_query,
                         doctor_availability=doctor_availability)

@patient_bp.route('/doctors/<int:doctor_id>')
@patient_required
def doctor_profile(doctor_id):
    """View doctor profile and availability"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get availability for next 7 days
    today = date.today()
    future_date = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= future_date,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    return render_template('patient/doctor_profile.html',
                         doctor=doctor,
                         availability=availability)

@patient_bp.route('/appointments/book/<int:doctor_id>', methods=['GET', 'POST'])
@patient_required
def book_appointment(doctor_id):
    """Book an appointment with a doctor"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        appointment_date_str = request.form.get('appointment_date')
        appointment_time_str = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        # Validate: check if date is in the future
        if appointment_date < date.today():
            flash('Cannot book appointments in the past.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        # Validate: check if slot is available (enhanced check)
        is_avail, msg = is_slot_available(doctor_id, appointment_date, appointment_time)
        if not is_avail:
            flash(f'Time slot not available: {msg}', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        # Validate: check if patient already has an appointment at this time
        existing_patient_appointment = Appointment.query.filter_by(
            patient_id=patient.id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            is_deleted=False
        ).filter(Appointment.status != 'Canceled').first()
        
        if existing_patient_appointment:
            flash('You already have an appointment at this time.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Booked'
        )
        db.session.add(appointment)
        db.session.commit()
        
        # Send email notification
        try:
            email_body = f"""
Dear {patient.full_name},

Your appointment has been confirmed!

Doctor: Dr. {doctor.full_name}
Specialization: {doctor.specialization}
Date: {appointment_date.strftime('%d %B %Y')}
Time: {appointment_time.strftime('%I:%M %p')}

Please arrive 10 minutes before your scheduled time.

Thank you,
Hospital Management System
            """
            send_email(
                subject='Appointment Confirmation',
                recipient=current_user.email,
                body=email_body
            )
        except Exception as e:
            pass  # Continue even if email fails
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.appointments'))
    
    # GET: Show booking form with available dates
    today = date.today()
    future_date = today + timedelta(days=7)
    
    available_dates = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= future_date,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    return render_template('patient/book_appointment.html',
                         doctor=doctor,
                         available_dates=available_dates)

@patient_bp.route('/appointments')
@patient_required
def appointments():
    """View all appointments"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    filter_type = request.args.get('filter', 'upcoming')
    
    query = Appointment.query.filter_by(patient_id=patient.id, is_deleted=False)
    
    if filter_type == 'upcoming':
        query = query.filter(
            Appointment.appointment_date >= date.today(),
            Appointment.status == 'Booked'
        )
    elif filter_type == 'past':
        query = query.filter(
            Appointment.status.in_(['Completed', 'Canceled'])
        )
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('patient/appointments.html',
                         appointments=appointments,
                         filter_type=filter_type)

@patient_bp.route('/appointments/cancel/<int:appointment_id>', methods=['POST'])
@patient_required
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify this appointment belongs to the logged-in patient
    if appointment.patient_id != patient.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'Booked':
        flash('Only booked appointments can be canceled.', 'warning')
        return redirect(url_for('patient.appointments'))
    
    appointment.status = 'Canceled'
    db.session.commit()
    
    # Send email notification
    try:
        email_body = f"""
Dear {patient.full_name},

Your appointment has been canceled.

Doctor: Dr. {appointment.doctor.full_name}
Date: {appointment.appointment_date.strftime('%d %B %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}

If you wish to reschedule, please book a new appointment.

Thank you,
Hospital Management System
        """
        send_email(
            subject='Appointment Canceled',
            recipient=current_user.email,
            body=email_body
        )
    except Exception as e:
        pass
    
    flash('Appointment has been canceled.', 'success')
    return redirect(url_for('patient.appointments'))

@patient_bp.route('/appointments/reschedule/<int:appointment_id>', methods=['GET', 'POST'])
@patient_required
def reschedule_appointment(appointment_id):
    """Reschedule an appointment"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify this appointment belongs to the logged-in patient
    if appointment.patient_id != patient.id:
        flash('You do not have permission to reschedule this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'Booked':
        flash('Only booked appointments can be rescheduled.', 'warning')
        return redirect(url_for('patient.appointments'))
    
    if request.method == 'POST':
        new_date_str = request.form.get('appointment_date')
        new_time_str = request.form.get('appointment_time')
        
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            new_time = datetime.strptime(new_time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('patient.reschedule_appointment', appointment_id=appointment_id))
        
        # Validate
        if new_date < date.today():
            flash('Cannot reschedule to a past date.', 'danger')
            return redirect(url_for('patient.reschedule_appointment', appointment_id=appointment_id))
        
        # Check if new slot is available
        if not is_slot_available(appointment.doctor_id, new_date, new_time):
            flash('This time slot is not available. Please choose another time.', 'danger')
            return redirect(url_for('patient.reschedule_appointment', appointment_id=appointment_id))
        
        # Update appointment
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        db.session.commit()
        
        flash('Appointment rescheduled successfully!', 'success')
        return redirect(url_for('patient.appointments'))
    
    # Get available dates for rescheduling
    today = date.today()
    future_date = today + timedelta(days=7)
    
    available_dates = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == appointment.doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= future_date,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    return render_template('patient/reschedule_appointment.html',
                         appointment=appointment,
                         available_dates=available_dates)

@patient_bp.route('/history')
@patient_required
def history():
    """View appointment history with treatments"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    # Get all completed appointments with treatments
    appointments = db.session.query(Appointment).filter_by(
        patient_id=patient.id,
        status='Completed',
        is_deleted=False
    ).order_by(Appointment.appointment_date.desc()).all()
    
    history_data = []
    for appointment in appointments:
        history_data.append({
            'appointment': appointment,
            'treatment': appointment.treatment
        })
    
    return render_template('patient/history.html', history_data=history_data)
