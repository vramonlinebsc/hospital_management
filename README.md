
# Hospital Management System

A comprehensive web-based Hospital Management System built with Flask for the MAD-1 (Modern Application Development) course project.

## 🏥 Features

### Admin Portal
- **Dashboard**: View statistics with real-time data and interactive charts (ChartJS)
  - Total doctors, patients, and appointments
  - Appointment trends visualization
  - Doctor-wise appointment distribution
- **Doctor Management**: Complete CRUD operations
  - Add, edit, delete/blacklist doctors
  - Manage doctor profiles, specializations, and availability
- **Patient Management**: Complete CRUD operations
  - Add, edit, delete/blacklist patients
  - View patient profiles and appointment history
- **Appointment Management**: View and manage all appointments
  - Filter by upcoming, past, or all appointments
  - View appointment details with treatment records
- **Advanced Search**: Search doctors and patients
  - Search by name, specialization, ID, contact number
  - Filter by doctor or patient type

### Doctor Portal
- **Dashboard**: Overview of appointments and patients
  - Today's appointments
  - This week's appointments
  - List of assigned patients
- **Appointment Management**:
  - View upcoming and completed appointments
  - Mark appointments as completed
  - Add treatment details (diagnosis, prescriptions, notes)
- **Patient History**: View complete medical history of patients
  - Previous diagnoses
  - Past prescriptions
  - Treatment notes
- **Availability Management**: Set availability for next 7 days
  - Define working hours for each day
  - Enable/disable availability per day
- **Profile**: View personal profile information

### Patient Portal
- **Registration & Login**: Self-registration capability
- **Dashboard**: Overview of appointments and quick actions
- **Doctor Search**: Find doctors by specialization and availability
  - Browse doctors by specialization
  - View doctor profiles and availability
  - Check consultation fees
- **Appointment Booking**:
  - Book appointments with available doctors
  - Select date and time slots
  - View doctor availability calendar
- **Appointment Management**:
  - View upcoming and past appointments
  - Reschedule appointments
  - Cancel appointments
- **Medical History**: View complete treatment history
  - Past diagnoses
  - Prescriptions
  - Doctor notes
- **Profile Management**: Update personal information
  - Contact details
  - Medical history
  - Allergies
  - Emergency contacts

### REST API
JSON endpoints for programmatic access:
- **Doctors**: GET, POST, PUT, DELETE `/api/doctors`
- **Patients**: GET, POST, PUT, DELETE `/api/patients`
- **Appointments**: GET, POST, PUT, DELETE `/api/appointments`
- **Statistics**: GET `/api/stats` (admin only)

All API endpoints return proper HTTP status codes and JSON responses.

### Additional Features
- **Email Notifications**: Automatic emails for appointment confirmations and cancellations
- **Form Validation**: Both frontend (HTML5, JavaScript) and backend validation
- **Responsive Design**: Mobile-friendly Bootstrap-based UI
- **Soft Delete**: All deletions use soft delete (is_deleted flag)
- **Role-Based Access Control**: Secure access using flask_login
- **Password Hashing**: Secure password storage using werkzeug.security
- **Configurable Settings**: Appointment slots and working hours
- **Pagination**: For long lists of records
- **Charts & Visualizations**: ChartJS for dashboard analytics

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite (created programmatically)
- **ORM**: Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **Frontend**: HTML5, CSS3, Bootstrap 5.3
- **Templating**: Jinja2
- **Charts**: Chart.js
- **Icons**: Bootstrap Icons

## 📁 Project Structure

```
hospital_management_system/
├── app.py                      # Main application file
├── config.py                   # Configuration settings
├── extensions.py               # Flask extensions initialization
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── hospital.db                 # SQLite database (auto-created)
├── models/                     # Database models
│   ├── __init__.py
│   ├── user.py                 # User model (authentication)
│   ├── doctor.py               # Doctor model
│   ├── patient.py              # Patient model
│   ├── appointment.py          # Appointment model
│   ├── treatment.py            # Treatment/medical record model
│   └── doctor_availability.py # Doctor availability model
├── routes/                     # Application routes
│   ├── __init__.py
│   ├── main.py                 # Main routes
│   ├── auth.py                 # Authentication routes
│   ├── admin.py                # Admin portal routes
│   ├── doctor.py               # Doctor portal routes
│   ├── patient.py              # Patient portal routes
│   └── api.py                  # REST API routes
├── templates/                  # HTML templates
│   ├── base.html               # Base template
│   ├── login.html
│   ├── register.html
│   ├── admin/                  # Admin templates
│   ├── doctor/                 # Doctor templates
│   ├── patient/                # Patient templates
│   └── errors/                 # Error pages
├── static/                     # Static files
│   ├── css/
│   │   └── style.css           # Custom CSS
│   ├── js/                     # JavaScript files
│   └── images/                 # Images
└── utils/                      # Utility functions
    ├── __init__.py
    ├── decorators.py           # Custom decorators
    └── helpers.py              # Helper functions
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Extract the Project
```bash
cd /path/to/hospital_management_system
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Email (Optional)
To enable email notifications, set environment variables:
```bash
export MAIL_USERNAME='your-email@gmail.com'
export MAIL_PASSWORD='your-app-password'
export MAIL_DEFAULT_SENDER='your-email@gmail.com'
```

Or edit `config.py` to add your email settings.

### Step 5: Run the Application
```bash
python app.py
```

The application will:
1. Create the database automatically (hospital.db)
2. Create tables programmatically
3. Create the admin user (username: admin, password: admin123)
4. Seed sample data (doctors, patients, appointments)
5. Start the development server

### Step 6: Access the Application
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

**Note**: This localhost refers to the computer running the application (not your local machine if you're accessing remotely). To access it locally or remotely, you'll need to deploy the application on your own system.

## 👥 Default Credentials

### Admin
- **Username**: admin
- **Password**: admin123

### Sample Doctor
- **Username**: dr.sharma
- **Password**: doctor123

### Sample Patient
- **Username**: patient1
- **Password**: patient123

## 📊 Database Schema

### Users Table
- Primary authentication table for all users
- Roles: admin, doctor, patient
- Password hashing with werkzeug.security

### Doctors Table
- Doctor profiles and information
- Links to Users table
- Specialization, qualification, experience
- Soft delete support (is_deleted flag)

### Patients Table
- Patient profiles and medical information
- Links to Users table
- Personal and medical details
- Soft delete support

### Appointments Table
- Appointment bookings
- Status: Booked, Completed, Canceled
- Links doctors and patients
- Prevents double booking

### Treatments Table
- Medical records for completed appointments
- Diagnosis, prescriptions, notes
- Follow-up information

### Doctor Availability Table
- Doctor's available time slots
- Configurable for next 7 days
- Start and end times per day

## 🔌 API Documentation

### Authentication
Most API endpoints require authentication. Use Flask-Login session or implement token-based auth.

### Endpoints

#### Doctors
```
GET    /api/doctors              - List all doctors
GET    /api/doctors/<id>         - Get doctor details
POST   /api/doctors              - Create doctor (admin)
PUT    /api/doctors/<id>         - Update doctor (admin)
DELETE /api/doctors/<id>         - Delete doctor (admin)
```

#### Patients
```
GET    /api/patients             - List all patients
GET    /api/patients/<id>        - Get patient details
POST   /api/patients             - Create patient (registration)
PUT    /api/patients/<id>        - Update patient
DELETE /api/patients/<id>        - Delete patient (admin)
```

#### Appointments
```
GET    /api/appointments         - List appointments
GET    /api/appointments/<id>    - Get appointment details
POST   /api/appointments         - Create appointment
PUT    /api/appointments/<id>    - Update appointment
DELETE /api/appointments/<id>    - Cancel appointment
```

#### Statistics
```
GET    /api/stats                - Get system statistics (admin)
```

### Example API Usage

```bash
# Get all doctors
curl http://localhost:5000/api/doctors

# Create appointment (requires authentication)
curl -X POST http://localhost:5000/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "appointment_date": "2025-11-15",
    "appointment_time": "10:00",
    "reason": "Regular checkup"
  }'
```

## ⚙️ Configuration

Edit `config.py` to customize:
- **APPOINTMENT_SLOT_DURATION**: Duration of each appointment slot (minutes)
- **WORKING_HOURS_START**: Start of working hours (24-hour format)
- **WORKING_HOURS_END**: End of working hours (24-hour format)
- **AVAILABLE_DAYS_AHEAD**: Number of days ahead for availability
- **ITEMS_PER_PAGE**: Pagination items per page
- **Email settings**: SMTP configuration

## 🔒 Security Features

- **Password Hashing**: All passwords are hashed using werkzeug.security
- **Role-Based Access**: Custom decorators for role-based authorization
- **Session Management**: Secure session handling with Flask-Login
- **CSRF Protection**: Form validation and CSRF tokens
- **Input Validation**: Backend and frontend validation
- **Soft Delete**: No data is permanently deleted

## 🧪 Testing

### Manual Testing
1. Register as a new patient
2. Login with different roles (admin, doctor, patient)
3. Test all CRUD operations
4. Book appointments and test workflow
5. Test API endpoints with curl or Postman

### Verification Checklist
- [ ] Admin can add/edit/delete doctors
- [ ] Admin can add/edit/delete patients
- [ ] Admin can view all appointments
- [ ] Admin search functionality works
- [ ] Doctor can view appointments
- [ ] Doctor can mark appointments as completed
- [ ] Doctor can add treatment details
- [ ] Doctor can set availability
- [ ] Patient can register
- [ ] Patient can search doctors
- [ ] Patient can book appointments
- [ ] Patient can view medical history
- [ ] Email notifications work (if configured)
- [ ] All API endpoints return correct responses
- [ ] Responsive design works on mobile

## 📝 Development Notes

### Code Quality
- All code is well-commented and documented
- Follows Flask best practices
- PEP 8 compliant Python code
- Clean separation of concerns (models, routes, templates)
- Reusable components and utilities

### Database
- Created programmatically (no manual DB Browser usage)
- All relationships properly defined
- Indexes on frequently queried fields
- Soft delete implementation throughout

### Frontend
- Bootstrap 5.3 for responsive design
- Custom CSS for enhanced styling
- Chart.js for data visualization
- HTML5 form validation
- JavaScript for dynamic interactions

## 🐛 Troubleshooting

### Database Issues
```bash
# Remove existing database and restart
rm hospital.db
python app.py
```

### Port Already in Use
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Email Not Working
- Check SMTP settings in config.py
- Verify email credentials
- For Gmail, use App Passwords

## 📦 Deployment

### For Production
1. Set `debug=False` in app.py
2. Use production WSGI server (gunicorn, uWSGI)
3. Set environment variables for secrets
4. Use PostgreSQL or MySQL instead of SQLite
5. Enable HTTPS

### Example with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📄 License

This project is created for educational purposes as part of the MAD-1 course.

## 👨‍💻 Author

Created as part of IIT Madras BS Degree Programme - Modern Application Development I Project

## 🙏 Acknowledgments

- Flask Documentation
- Bootstrap Documentation
- Chart.js Documentation
- IIT Madras BS Degree Programme

## 📧 Support

For issues and questions, please refer to:
- Flask documentation: https://flask.palletsprojects.com/
- SQLAlchemy documentation: https://docs.sqlalchemy.org/
- Bootstrap documentation: https://getbootstrap.com/

---

**Note**: This application is designed to run on your local machine. The database is created automatically, and all setup is programmatic as per project requirements.
