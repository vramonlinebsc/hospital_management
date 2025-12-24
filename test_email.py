from app import create_app
from extensions import mail
from flask_mail import Message

app = create_app()

print("📧 Sending test email...")
print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

with app.app_context():
    try:
        msg = Message(
            subject='Test Email from HMS',
            recipients=['test@example.com'],
            body='This is a test email. If you see this in Mailtrap, email is working!',
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        print("✅ Test email sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()