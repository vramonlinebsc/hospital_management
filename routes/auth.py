
"""
Authentication routes for login, logout, and registration
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from extensions import db
from models.user import User
from models.patient import Patient
from routes import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash(f"DEBUG: found user id={user.id} username={user.username} role={getattr(user,'role',None)} is_active={getattr(user,'is_active',None)}", 'info')
        else:
            flash("DEBUG: no user found for that username", 'warning')
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=request.form.get('remember', False))
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_doctor():
                return redirect(url_for('doctor.dashboard'))
            elif user.is_triage():
               return redirect(url_for('triage.dashboard'))
            else:
                return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create user account
        user = User(username=username, email=email, role='patient')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            full_name=full_name,
            contact_number=contact_number
        )
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
