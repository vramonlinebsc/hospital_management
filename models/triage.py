# models/triage.py
from extensions import db
from datetime import datetime

class Triage(db.Model):
    __tablename__ = 'triages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    contact_number = db.Column(db.String(30), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Triage {self.full_name} (user_id={self.user_id})>'