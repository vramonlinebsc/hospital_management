# migrate_triage.py
"""
Database migration script to add triage functionality
Run this once: python migrate_triage.py
"""
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting database migration for triage integration...")
    
    try:
        # Check if triage_assessments table exists
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='triage_assessments'"
        )).fetchone()
        
        if not result:
            print("\n1. Creating triage_assessments table...")
            db.session.execute(text("""
                CREATE TABLE triage_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    triage_user_id INTEGER NOT NULL,
                    patient_id INTEGER,
                    patient_name VARCHAR(100) NOT NULL,
                    patient_contact VARCHAR(20),
                    patient_age INTEGER,
                    patient_gender VARCHAR(10),
                    chief_complaint TEXT NOT NULL,
                    vital_signs TEXT,
                    priority_level VARCHAR(20) NOT NULL,
                    recommended_specialization VARCHAR(100),
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'Pending' NOT NULL,
                    assigned_doctor_id INTEGER,
                    appointment_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (triage_user_id) REFERENCES triages (id),
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (assigned_doctor_id) REFERENCES doctors (id),
                    FOREIGN KEY (appointment_id) REFERENCES appointments (id)
                )
            """))
            print("   ✓ triage_assessments table created")
        else:
            print("\n1. triage_assessments table already exists - skipping")
        
        # Check if priority column exists in appointments table
        result = db.session.execute(text(
            "PRAGMA table_info(appointments)"
        )).fetchall()
        
        column_names = [row[1] for row in result]
        
        if 'priority' not in column_names:
            print("\n2. Adding 'priority' column to appointments table...")
            db.session.execute(text(
                "ALTER TABLE appointments ADD COLUMN priority VARCHAR(20) DEFAULT 'Standard'"
            ))
            print("   ✓ priority column added")
        else:
            print("\n2. priority column already exists - skipping")
        
        if 'triage_assessment_id' not in column_names:
            print("\n3. Adding 'triage_assessment_id' column to appointments table...")
            db.session.execute(text(
                "ALTER TABLE appointments ADD COLUMN triage_assessment_id INTEGER"
            ))
            print("   ✓ triage_assessment_id column added")
        else:
            print("\n3. triage_assessment_id column already exists - skipping")
        
        db.session.commit()
        print("\n" + "="*60)
        print("✓ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now proceed to Step 2.")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n✗ ERROR: {str(e)}")
        print("Migration failed. Please report this error.")
        raise

if __name__ == '__main__':
    pass