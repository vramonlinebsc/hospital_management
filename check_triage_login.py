# check_triage_login.py
# Run: python check_triage_login.py

from app import create_app
app = create_app()

from extensions import db
from models.user import User

USERNAME_OR_EMAIL = "triage1"
PASSWORD = "pass1234"

with app.app_context():
    user = User.query.filter((User.username == USERNAME_OR_EMAIL) | (User.email == USERNAME_OR_EMAIL)).first()
    if not user:
        print("NO_USER_FOUND")
    else:
        print("FOUND_USER:", user.id, user.username, user.email, "role=", getattr(user, 'role', None), "is_active=", getattr(user, 'is_active', None))
        # Print stored password/hash field names we can find
        possible_hash_attrs = ['password', 'password_hash', 'pw_hash', 'pass_hash']
        for a in possible_hash_attrs:
            if hasattr(user, a):
                print(f"HASH_FIELD {a}:", getattr(user, a))

        # Try common check/verify methods
        tried = False
        for method_name in dir(user):
            if any(k in method_name.lower() for k in ('check', 'verify', 'authenticate')) and callable(getattr(user, method_name)):
                tried = True
                print("TRY_METHOD:", method_name)
                try:
                    result = getattr(user, method_name)(PASSWORD)
                    print(" -> returned:", result)
                except Exception as e:
                    print(" -> raised:", repr(e))

        if not tried:
            print("No obvious check/verify methods found on user object.")

        # As a last resort print repr of user to inspect fields
        try:
            print("user repr:", repr(user))
        except Exception:
            pass
