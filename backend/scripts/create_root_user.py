"""
Script to create or update a user to root role
"""
import database as db
import DBmodels
import sys
from auth_utils import hash_password

def create_or_update_root_user(email: str = None):
    """Create a root user or update existing user to root"""
    session = db.SessionLocal()
    try:
        if email:
            # Update existing user to root
            user = session.query(DBmodels.User).filter(DBmodels.User.email == email).first()
            if user:
                user.role = 'root'
                session.commit()
                print(f"✓ Updated user {email} to root role")
                return user
            else:
                print(f"✗ User with email {email} not found")
                return None
        else:
            # Create a new root user
            print("Creating a new root user...")
            print("Please provide email, password, and name:")
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            name = input("Name: ").strip()
            
            # Check if user already exists
            existing = session.query(DBmodels.User).filter(DBmodels.User.email == email).first()
            if existing:
                existing.role = 'root'
                session.commit()
                print(f"✓ Updated existing user {email} to root role")
                return existing
            
            # Create new user
            new_user = DBmodels.User(
                email=email,
                hashed_password=hash_password(password),
                name=name,
                role='root',
                is_active=True,
                is_blocked=False
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            print(f"✓ Created root user: {email} (ID: {new_user.id})")
            return new_user
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {str(e)}")
        return None
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
        create_or_update_root_user(email)
    else:
        create_or_update_root_user()

