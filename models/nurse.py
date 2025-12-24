# models/nurse.py
from extensions import db
from datetime import datetime

class Nurse(db.Model):
    __tablename__ = 'nurses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    contact_number = db.Column(db.String(30), nullable=True)
    department = db.Column(db.String(120), nullable=True)

    # Comma-separated doctor IDs assigned to this nurse (e.g. "1,5,9")
    assigned_doctors = db.Column(db.Text, nullable=True, default='')

    # Optional one-to-one assignment to a patient
    assigned_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_assigned_patient(self):
        """Return assigned Patient instance or None"""
        if not self.assigned_patient_id:
            return None
        # local import to avoid circular import at module load time
        from models.patient import Patient
        return Patient.query.get(self.assigned_patient_id)

    def assign_patient(self, patient_id):
        """Assign this nurse to a patient (app-level check required before calling)"""
        self.assigned_patient_id = int(patient_id)

    def get_assigned_doctor_ids(self):
        """Return assigned doctor IDs as a list of ints"""
        if not self.assigned_doctors:
            return []
        return [int(x) for x in self.assigned_doctors.split(',') if x.strip().isdigit()]

    def set_assigned_doctor_ids(self, id_list):
        """Store assigned doctor IDs from an iterable of ints/strings"""
        ids = [str(int(x)) for x in id_list if str(x).strip().isdigit()]
        self.assigned_doctors = ','.join(ids)

    def __repr__(self):
        return f'<Nurse {self.full_name} (user_id={self.user_id})>'