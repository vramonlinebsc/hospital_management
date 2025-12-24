
"""
Hospital Management System - Main Application
Flask web application for managing hospital operations
"""
from flask import Flask, render_template
from config import Config
from extensions import db, init_extensions
from datetime import datetime


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    init_extensions(app)
    

    
    # Register blueprints
    from routes import main_bp, auth_bp, admin_bp, doctor_bp, patient_bp, api_bp, triage_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(triage_bp)
    
    # Template filters
    @app.template_filter('format_date')
    def format_date_filter(date_obj):
        """Format date for display"""
        if not date_obj:
            return ''
        return date_obj.strftime('%d %b %Y')
    
    @app.template_filter('format_time')
    def format_time_filter(time_obj):
        """Format time for display"""
        if not time_obj:
            return ''
        return time_obj.strftime('%I:%M %p')
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_obj):
        """Format datetime for display"""
        if not datetime_obj:
            return ''
        return datetime_obj.strftime('%d %b %Y %I:%M %p')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processor for current year
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app

def init_database():
    """Initialize database with tables and seed data"""
    from models.user import User
    from models.doctor import Doctor
    from models.patient import Patient
    from models.appointment import Appointment
    from models.treatment import Treatment
    from models.doctor_availability import DoctorAvailability
    from datetime import date, time, timedelta
    
    # Create all tables
    db.create_all()
    
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("Creating admin user...")
        # Create admin user
        admin = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            role='admin',
            is_active=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created - Username: {Config.ADMIN_USERNAME}, Password: {Config.ADMIN_PASSWORD}")
    
    # Seed sample data if no doctors exist
    if Doctor.query.count() == 0:
        print("Seeding sample data...")
        
        # Create sample doctors
        doctors_data = [
            {
                'username': 'dr.sharma',
                'email': 'sharma@hospital.com',
                'password': 'doctor123',
                'full_name': 'Dr. Rajesh Sharma',
                'specialization': 'Cardiology',
                'qualification': 'MBBS, MD (Cardiology)',
                'experience_years': 15,
                'contact_number': '+91-9876543210',
                'license_number': 'MCI-12345',
                'consultation_fee': 800.0,
                'bio': 'Experienced cardiologist with 15 years of practice.'
            },
            {
                'username': 'dr.patel',
                'email': 'patel@hospital.com',
                'password': 'doctor123',
                'full_name': 'Dr. Priya Patel',
                'specialization': 'Pediatrics',
                'qualification': 'MBBS, MD (Pediatrics)',
                'experience_years': 10,
                'contact_number': '+91-9876543211',
                'license_number': 'MCI-12346',
                'consultation_fee': 600.0,
                'bio': 'Specialized in child healthcare and development.'
            },
            {
                'username': 'dr.kumar',
                'email': 'kumar@hospital.com',
                'password': 'doctor123',
                'full_name': 'Dr. Amit Kumar',
                'specialization': 'Orthopedics',
                'qualification': 'MBBS, MS (Orthopedics)',
                'experience_years': 12,
                'contact_number': '+91-9876543212',
                'license_number': 'MCI-12347',
                'consultation_fee': 700.0,
                'bio': 'Expert in bone and joint treatments.'
            },
            {
                'username': 'dr.singh',
                'email': 'singh@hospital.com',
                'password': 'doctor123',
                'full_name': 'Dr. Meera Singh',
                'specialization': 'Dermatology',
                'qualification': 'MBBS, MD (Dermatology)',
                'experience_years': 8,
                'contact_number': '+91-9876543213',
                'license_number': 'MCI-12348',
                'consultation_fee': 500.0,
                'bio': 'Specialist in skin, hair, and nail disorders.'
            }
        ]
        
        for doc_data in doctors_data:
            user = User(
                username=doc_data['username'],
                email=doc_data['email'],
                role='doctor'
            )
            user.set_password(doc_data['password'])
            db.session.add(user)
            db.session.flush()
            
            doctor = Doctor(
                user_id=user.id,
                full_name=doc_data['full_name'],
                specialization=doc_data['specialization'],
                qualification=doc_data['qualification'],
                experience_years=doc_data['experience_years'],
                contact_number=doc_data['contact_number'],
                license_number=doc_data['license_number'],
                consultation_fee=doc_data['consultation_fee'],
                bio=doc_data['bio']
            )
            db.session.add(doctor)
            db.session.flush()  # Flush to get doctor.id
            
            # Add availability for next 7 days
            for i in range(7):
                avail_date = date.today() + timedelta(days=i)
                availability = DoctorAvailability(
                    doctor_id=doctor.id,
                    available_date=avail_date,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    is_available=True
                )
                db.session.add(availability)
        
        # Create sample patients
        patients_data = [
            {
                'username': 'patient1',
                'email': 'patient1@example.com',
                'password': 'patient123',
                'full_name': 'Rahul Verma',
                'contact_number': '+91-9123456789',
                'date_of_birth': date(1990, 5, 15),
                'gender': 'Male',
                'blood_group': 'O+'
            },
            {
                'username': 'patient2',
                'email': 'patient2@example.com',
                'password': 'patient123',
                'full_name': 'Anjali Gupta',
                'contact_number': '+91-9123456790',
                'date_of_birth': date(1985, 8, 20),
                'gender': 'Female',
                'blood_group': 'A+'
            },
            {
                'username': 'patient3',
                'email': 'patient3@example.com',
                'password': 'patient123',
                'full_name': 'Vikram Reddy',
                'contact_number': '+91-9123456791',
                'date_of_birth': date(1995, 3, 10),
                'gender': 'Male',
                'blood_group': 'B+'
            }
        ]
        
        for pat_data in patients_data:
            user = User(
                username=pat_data['username'],
                email=pat_data['email'],
                role='patient'
            )
            user.set_password(pat_data['password'])
            db.session.add(user)
            db.session.flush()
            
            patient = Patient(
                user_id=user.id,
                full_name=pat_data['full_name'],
                contact_number=pat_data['contact_number'],
                date_of_birth=pat_data['date_of_birth'],
                gender=pat_data['gender'],
                blood_group=pat_data['blood_group']
            )
            db.session.add(patient)
        
        db.session.commit()
        print("Sample data seeded successfully!")
        print("\nSample Credentials:")
        print("Admin - Username: admin, Password: admin123")
        print("Doctor - Username: dr.sharma, Password: doctor123")
        print("Patient - Username: patient1, Password: patient123")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Initialize database
        init_database()
    
    # Run the application
    print("\n" + "="*60)
    print("Hospital Management System Starting...")
    print("="*60)
    print("\nAccess the application at: http://127.0.0.1:5000")
    print("\nDefault Admin Credentials:")
    print(f"  Username: {Config.ADMIN_USERNAME}")
    print(f"  Password: {Config.ADMIN_PASSWORD}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
