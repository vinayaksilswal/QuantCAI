"""Quick script to update a user to root role"""
import database as db
import DBmodels

# Update alice.johnson@example.com to root
session = db.SessionLocal()
try:
    user = session.query(DBmodels.User).filter(DBmodels.User.email == 'alice.johnson@example.com').first()
    if user:
        user.role = 'root'
        session.commit()
        print(f"✓ Updated {user.email} to root role (ID: {user.id})")
    else:
        print("User not found")
        
    # Show all root users
    root_users = session.query(DBmodels.User).filter(DBmodels.User.role == 'root').all()
    print(f"\nTotal root users: {len(root_users)}")
    for u in root_users:
        print(f"  - {u.email} (ID: {u.id})")
except Exception as e:
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()

