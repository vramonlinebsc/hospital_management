# celery_config.py
"""
Celery configuration for background tasks
"""
from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    """Create Celery instance tied to Flask app"""
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    
    # Update Celery config from Flask config
    celery.conf.update(
        result_expires=3600,
        timezone='Asia/Kolkata',
        enable_utc=False,
        broker_connection_retry_on_startup=True
    )
    
    # Scheduled tasks configuration
    celery.conf.beat_schedule = {
        'send-daily-reminders': {
            'task': 'tasks.send_daily_appointment_reminders',
            'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
        },
        'send-monthly-reports': {
            'task': 'tasks.send_monthly_doctor_reports',
            'schedule': crontab(day_of_month=1, hour=10, minute=0),  # 1st of every month at 10 AM
        },
    }
    
    # Bind Flask app context to Celery tasks
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery