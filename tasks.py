# tasks.py
"""
Celery background tasks for Hospital Management System
"""
from celery import Celery
from app import create_app
from extensions import db, mail
from flask_mail import Message
from models.appointment import Appointment
from models.doctor import Doctor
from models.patient import Patient
from models.treatment import Treatment
from datetime import datetime, date, timedelta
from sqlalchemy import func
from celery.schedules import crontab

# Create app and celery instance
# Create app and celery instance
flask_app = create_app()


# Create Celery instance directly
celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery.conf.update(
    result_expires=3600,
    timezone='Asia/Kolkata',
    enable_utc=False,
    broker_connection_retry_on_startup=True
)

# Scheduled tasks configuration
celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'tasks.send_daily_appointment_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    'send-monthly-reports': {
        'task': 'tasks.send_monthly_doctor_reports',
        'schedule': crontab(day_of_month=1, hour=10, minute=0),
    },
}



@celery.task(name='tasks.send_daily_appointment_reminders')
def send_daily_appointment_reminders():
    """
    Scheduled task: Send appointment reminders to patients
    Runs daily at 9 AM
    """
    with flask_app.app_context():
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Get appointments for today and tomorrow
        upcoming_appointments = Appointment.query.filter(
            Appointment.appointment_date.in_([today, tomorrow]),
            Appointment.status == 'Booked',
            Appointment.is_deleted == False
        ).all()
        
        sent_count = 0
        for appointment in upcoming_appointments:
            try:
                patient = appointment.patient
                doctor = appointment.doctor
                
                # Calculate days until appointment
                days_until = (appointment.appointment_date - today).days
                subject = f"Appointment Reminder - {'Today' if days_until == 0 else 'Tomorrow'}"
                
                # Email body
                body = f"""
Dear {patient.full_name},

This is a friendly reminder about your upcoming appointment:

Doctor: Dr. {doctor.full_name}
Specialization: {doctor.specialization}
Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}

{'Your appointment is TODAY. ' if days_until == 0 else 'Your appointment is TOMORROW. '}Please arrive 10 minutes early.

If you need to cancel or reschedule, please log in to your account.

Thank you,
Hospital Management System
                """
                
                msg = Message(
                    subject=subject,
                    recipients=[patient.user.email],
                    body=body
                )
                mail.send(msg)
                sent_count += 1
                
            except Exception as e:
                print(f"Error sending reminder to patient {patient.id}: {str(e)}")
                continue
        
        return f"Sent {sent_count} appointment reminders"


@celery.task(name='tasks.send_monthly_doctor_reports')
def send_monthly_doctor_reports():
    """
    Scheduled task: Send monthly appointment reports to doctors
    Runs on 1st of every month at 10 AM
    """
    with flask_app.app_context():
        today = date.today()
        last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        
        doctors = Doctor.query.filter_by(is_deleted=False, is_active=True).all()
        
        sent_count = 0
        for doctor in doctors:
            try:
                # Get doctor's appointments for last month
                appointments = Appointment.query.filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.appointment_date >= last_month_start,
                    Appointment.appointment_date <= last_month_end,
                    Appointment.is_deleted == False
                ).all()
                
                # Calculate statistics
                total_appointments = len(appointments)
                completed = sum(1 for a in appointments if a.status == 'Completed')
                canceled = sum(1 for a in appointments if a.status == 'Canceled')
                
                # Count by priority
                emergency = sum(1 for a in appointments if a.priority == 'Emergency')
                urgent = sum(1 for a in appointments if a.priority == 'Urgent')
                
                # Email body
                subject = f"Monthly Appointment Report - {last_month_start.strftime('%B %Y')}"
                body = f"""
Dear Dr. {doctor.full_name},

Here is your appointment summary for {last_month_start.strftime('%B %Y')}:

STATISTICS:
-----------
Total Appointments: {total_appointments}
Completed: {completed}
Canceled: {canceled}
No-shows: {total_appointments - completed - canceled}

PRIORITY BREAKDOWN:
-------------------
Emergency Cases: {emergency}
Urgent Cases: {urgent}
Standard Cases: {total_appointments - emergency - urgent}

PATIENT DETAILS:
----------------
"""
                
                # Add appointment details
                for apt in appointments[:10]:  # Show first 10
                    body += f"\n- {apt.appointment_date.strftime('%d %b')}: {apt.patient.full_name} ({apt.status})"
                
                if total_appointments > 10:
                    body += f"\n... and {total_appointments - 10} more appointments"
                
                body += """

Thank you for your dedication!

Best regards,
Hospital Management System
                """
                
                msg = Message(
                    subject=subject,
                    recipients=[doctor.user.email],
                    body=body
                )
                mail.send(msg)
                sent_count += 1
                
            except Exception as e:
                print(f"Error sending report to doctor {doctor.id}: {str(e)}")
                continue
        
        return f"Sent {sent_count} monthly reports to doctors"


@celery.task(name='tasks.send_treatment_summary')
def send_treatment_summary(appointment_id):
    """
    User-triggered task: Send treatment summary email after appointment completion
    """
    with flask_app.app_context():
        try:
            from flask_mail import Message as MailMessage
            
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return f"Appointment {appointment_id} not found"
            
            patient = appointment.patient
            doctor = appointment.doctor
            treatment = appointment.treatment
            
            if not treatment:
                return f"No treatment found for appointment {appointment_id}"
            
            # Email to patient
            subject = f"Treatment Summary - Appointment on {appointment.appointment_date.strftime('%d %b %Y')}"
            
            patient_body = f"""
Dear {patient.full_name},

Here is the summary of your recent appointment:

APPOINTMENT DETAILS:
--------------------
Doctor: Dr. {doctor.full_name}
Specialization: {doctor.specialization}
Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}

DIAGNOSIS:
----------
{treatment.diagnosis}

PRESCRIPTION:
-------------
{treatment.prescription if treatment.prescription else 'None prescribed'}

TESTS RECOMMENDED:
------------------
{treatment.test_recommended if treatment.test_recommended else 'None'}

NOTES:
------
{treatment.notes if treatment.notes else 'None'}

"""
            
            if treatment.follow_up_required and treatment.follow_up_date:
                patient_body += f"""
FOLLOW-UP:
----------
Please schedule a follow-up appointment on or after {treatment.follow_up_date.strftime('%d %B %Y')}.
"""
            
            patient_body += """
If you have any questions, please contact us or log in to your account.

Take care,
Hospital Management System
            """
            
            # Create and send message
            msg = MailMessage(
                subject=subject,
                recipients=[patient.user.email],
                body=patient_body,
                sender=flask_app.config['MAIL_DEFAULT_SENDER']
            )
            
            with flask_app.app_context():
                mail.send(msg)
            
            print(f"✅ Email sent successfully to {patient.user.email}")
            return f"Treatment summary sent to patient {patient.id}"
            
        except Exception as e:
            print(f"❌ Email error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error sending treatment summary: {str(e)}"
        
        
# tasks.py

# ... all your existing code ...

@celery.task(name='tasks.send_treatment_summary')
def send_treatment_summary(appointment_id):
    # ... existing code ...
    pass

# ✅ ADD THE TEST TASK HERE (at the very end)
@celery.task(name='tasks.test_mailtrap')
def test_mailtrap():
    """Test if Mailtrap is configured correctly"""
    with flask_app.app_context():
        print("="*50)
        print("📧 EMAIL CONFIGURATION:")
        print(f"Server: {flask_app.config['MAIL_SERVER']}")
        print(f"Port: {flask_app.config['MAIL_PORT']}")
        print(f"Username: {flask_app.config['MAIL_USERNAME']}")
        print(f"TLS: {flask_app.config['MAIL_USE_TLS']}")
        print("="*50)
        
        # Send test email
        msg = Message(
            subject="Test Email from Mailtrap",
            recipients=["test@example.com"],
            body="This is a test email to verify Mailtrap configuration."
        )
        mail.send(msg)
        return "Test email sent to Mailtrap!"