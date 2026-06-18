import os
import sys
from sqlalchemy import text

# Add the parent directory to Python path to import core config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import sync_engine

def run_migrations():
    # 1. Update PG enum type outside of a transaction block
    enum_queries = [
        "ALTER TYPE usage_event_type_enum ADD VALUE IF NOT EXISTS 'qpu_run';"
    ]
    raw_conn = sync_engine.raw_connection()
    try:
        raw_conn.set_isolation_level(0) # AUTOCOMMIT
        cursor = raw_conn.cursor()
        print("Adding 'qpu_run' value to usage_event_type_enum...")
        for q in enum_queries:
            try:
                cursor.execute(q)
                print(f"Executed enum query successfully: {q}")
            except Exception as e:
                print(f"Informational/Error running enum query: {e}")
    finally:
        raw_conn.close()

    # 2. Create tables inside a transaction block
    table_queries = [
        """
        CREATE TABLE IF NOT EXISTS monitored_targets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_type VARCHAR(50) NOT NULL,
            target_value VARCHAR(500) NOT NULL,
            schedule_interval VARCHAR(50) DEFAULT 'daily' NOT NULL,
            last_scan_score DOUBLE PRECISION,
            last_scanned_at TIMESTAMP WITH TIME ZONE
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_monitored_targets_user_id ON monitored_targets(user_id);",
        """
        CREATE TABLE IF NOT EXISTS security_alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_id INTEGER REFERENCES monitored_targets(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_security_alerts_user_id ON security_alerts(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_security_alerts_target_id ON security_alerts(target_id);"
    ]

    with sync_engine.begin() as conn:
        print("Starting Phase 3 table database migrations...")
        for q in table_queries:
            try:
                conn.execute(text(q))
                print(f"Executed query successfully: {q.strip()[:60]}...")
            except Exception as e:
                print(f"Error executing query {q.strip()[:60]}...: {e}")
        print("Phase 3 migrations finished.")

if __name__ == "__main__":
    run_migrations()
