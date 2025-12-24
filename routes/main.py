
"""
Main routes for landing pages
"""
from flask import render_template, redirect, url_for
from flask import render_template_string
from flask_login import current_user
from routes import main_bp

@main_bp.route('/')
def index():
    """Landing page - redirect based on user role"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_doctor():
            return redirect(url_for('doctor.dashboard'))
        elif current_user.is_triage():
            return redirect(url_for('triage.dashboard'))
        elif current_user.is_patient():
            return redirect(url_for('patient.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

