import database as db
import DBmodels
from auth_utils import hash_password

def create_test_user():
    session = db.SessionLocal()
    email = "test@example.com"
    try:
        user = session.query(DBmodels.User).filter(DBmodels.User.email == email).first()
        if user:
            print(f"User {email} already exists.")
            return

        new_user = DBmodels.User(
            email=email,
            password=hash_password("password123"),
            name="Test User",
            role="root",
            is_active=True,
            is_blocked=False
        )
        session.add(new_user)
        session.commit()
        print(f"Created user {email}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_test_user()
