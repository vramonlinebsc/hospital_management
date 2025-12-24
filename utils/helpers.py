
"""
Helper functions for common operations
"""
from datetime import datetime, timedelta, time
from flask import current_app
from flask_mail import Message

def send_email(subject, recipient, body, html_body=None):
    """
    Send email notification
    Note: Requires Flask-Mail configuration
    """
    try:
        from extensions import mail
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        if html_body:
            msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        return False

def generate_time_slots(start_hour, end_hour, slot_duration):
    """
    Generate time slots for appointments
    
    Args:
        start_hour: Starting hour (e.g., 9 for 9 AM)
        end_hour: Ending hour (e.g., 17 for 5 PM)
        slot_duration: Duration in minutes (e.g., 30)
    
    Returns:
        List of time objects
    """
    slots = []
    current_time = datetime.combine(datetime.today(), time(start_hour, 0))
    end_time = datetime.combine(datetime.today(), time(end_hour, 0))
    
    while current_time < end_time:
        slots.append(current_time.time())
        current_time += timedelta(minutes=slot_duration)
    
    return slots

def is_slot_available(doctor_id, appointment_date, appointment_time, end_time=None,
                      slot_minutes=30, exclude_appointment_id=None):
    """
    Check if a slot is available for booking/rescheduling.

    Backward-compatible: original calls that pass (doctor_id, appointment_date, appointment_time)
    will be treated as start_time with default slot_minutes (30) used to compute end_time.

    Params:
      - doctor_id: int
      - appointment_date: datetime.date
      - appointment_time: datetime.time (start time)
      - end_time: (optional) datetime.time (end time)
      - slot_minutes: used when end_time is None (default 30)
      - exclude_appointment_id: (optional) int - appointment id to ignore (useful for reschedule)

    Returns:
      (available: bool, message: str)
    """
    # Import models locally to avoid import cycles
    from extensions import db
    from models.appointment import Appointment
    from models.doctor_availability import DoctorAvailability

    # Normalize new slot datetimes
    new_start = datetime.combine(appointment_date, appointment_time)
    if end_time:
        new_end = datetime.combine(appointment_date, end_time)
    else:
        new_end = new_start + timedelta(minutes=slot_minutes)

    # 1) Check existing appointments for the same doctor on that date for overlaps
    q = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.is_deleted == False
    ).filter(
        Appointment.status != 'Canceled'
    )
    if exclude_appointment_id:
        q = q.filter(Appointment.id != exclude_appointment_id)

    existing = q.all()

    for ap in existing:
        ap_start = datetime.combine(ap.appointment_date, ap.appointment_time)

        # Determine appointment end time if available
        ap_end = None
        if hasattr(ap, 'appointment_end_time') and getattr(ap, 'appointment_end_time'):
            ap_end = datetime.combine(ap.appointment_date, ap.appointment_end_time)
        elif hasattr(ap, 'duration_minutes') and getattr(ap, 'duration_minutes'):
            ap_end = ap_start + timedelta(minutes=ap.duration_minutes)
        else:
            # fallback to supplied default slot length
            ap_end = ap_start + timedelta(minutes=slot_minutes)

        # Overlap check: return False if intervals overlap
        if not (ap_end <= new_start or ap_start >= new_end):
            return False, f"Conflicts with existing appointment at {ap_start.time().strftime('%H:%M')}"

    # 2) Verify doctor has availability records for that date and that the requested slot
    #    falls entirely within at least one availability block.
    avail_blocks = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        available_date=appointment_date,
        is_available=True
    ).all()

    if not avail_blocks:
        return False, "Doctor not available on this date"

    inside_any = False
    for a in avail_blocks:
        a_start = datetime.combine(a.available_date, a.start_time)
        a_end = datetime.combine(a.available_date, a.end_time)
        if new_start >= a_start and new_end <= a_end:
            inside_any = True
            break

    if not inside_any:
        return False, "Requested time is outside doctor's availability"

    # Passed all checks
    return True, "Slot available"

def format_date(date_obj):
    """Format date for display"""
    if not date_obj:
        return ''
    return date_obj.strftime('%d %b %Y')

def format_time(time_obj):
    """Format time for display"""
    if not time_obj:
        return ''
    return time_obj.strftime('%I:%M %p')

def format_datetime(datetime_obj):
    """Format datetime for display"""
    if not datetime_obj:
        return ''
    return datetime_obj.strftime('%d %b %Y %I:%M %p')

def get_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    today = datetime.today().date()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age
