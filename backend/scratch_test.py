import os
import sys
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

# Add backend dir to sys path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.auth import get_subscription_plan_sync
import models as DBmodels

db = SessionLocal()
try:
    # Get a user from the database
    user = db.query(DBmodels.User).first()
    if user:
        print(f"Testing for user: {user.email} (ID: {user.id})")
        plan = get_subscription_plan_sync(db, user.id, user.org_id)
        print(f"Subscription plan: {plan}")
    else:
        print("No users found in database.")
except Exception as e:
    print(f"Error occurred: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
