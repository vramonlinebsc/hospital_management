
"""
Utility functions and helpers for Hospital Management System
"""
from utils.decorators import admin_required, doctor_required, patient_required
from utils.helpers import send_email, generate_time_slots, is_slot_available
