import database as db
import DBmodels
from sqlalchemy import text

def clean_database():
    session = db.SessionLocal()
    try:
        print("Cleaning up users with potential bad password hashes...")
        # Since we switched hashing, existing users might have issues if their passwords weren't hashed correctly
        # But safest is to just delete the user 'vinayaksilswal@gmail.com' who was having trouble
        
        email_to_delete = "vinayaksilswal@gmail.com"
        users = session.query(DBmodels.User).filter(DBmodels.User.email == email_to_delete).all()
        
        if users:
            for user in users:
                print(f"Deleting user: {user.email} (ID: {user.id})")
                session.delete(user)
            session.commit()
            print("Cleanup successful.")
        else:
            print(f"User {email_to_delete} not found.")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clean_database()
