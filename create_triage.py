# create_triage.py
# Run: python create_triage.py

from app import create_app
app = create_app()

from extensions import db
from models.user import User
from models.triage import Triage
from datetime import datetime

USERNAME = "triage"
EMAIL = "triage@iithealth.com"
PASSWORD = "triage1234"
FULL_NAME = "Triage User"
CONTACT = "9999999999"
DEPARTMENT = "Triage Desk"

with app.app_context():
    existing = User.query.filter((User.username == USERNAME) | (User.email == EMAIL)).first()
    if existing:
        print(f"User already exists: id={existing.id} username={existing.username} email={existing.email} role={existing.role}")
    else:
        u = User(username=USERNAME, email=EMAIL, role='triage')
        u.set_password(PASSWORD)
        u.is_active = True
        db.session.add(u)
        db.session.flush()  # ensures u.id is available

        t = Triage(
            user_id=u.id,
            full_name=FULL_NAME,
            contact_number=CONTACT,
            department=DEPARTMENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(t)
        db.session.commit()
        print(f"Created triage user: id={u.id} username={u.username} email={u.email}")
        print(f"Login with username/email and password: {PASSWORD}")