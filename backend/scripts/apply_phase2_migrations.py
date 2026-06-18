import os
import sys
from sqlalchemy import text

# Add parent directory to path to import core config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import sync_engine

def run_migrations():
    # PostgreSQL requires commit after each ALTER TYPE ADD VALUE statement,
    # and they cannot run inside transaction blocks. We run them with autocommit.
    queries = [
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'security_analyst';",
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'compliance_officer';",
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'org_admin';"
    ]
    
    # Using raw connection to execute ALTER TYPE outside of a transaction block
    raw_conn = sync_engine.raw_connection()
    try:
        raw_conn.set_isolation_level(0) # AUTOCOMMIT
        cursor = raw_conn.cursor()
        print("Starting phase 2 database migrations...")
        for q in queries:
            try:
                cursor.execute(q)
                print(f"Executed query successfully: {q}")
            except Exception as e:
                # Alter types might throw error if running against SQLite or if value already exists
                print(f"Informational/Error running query: {e}")
        print("Phase 2 migrations finished.")
    finally:
        raw_conn.close()

if __name__ == "__main__":
    run_migrations()
