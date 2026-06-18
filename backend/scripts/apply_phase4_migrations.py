import os
import sys
from sqlalchemy import text

# Add the parent directory to Python path to import core config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import sync_engine

def run_migrations():
    table_queries = [
        """
        ALTER TABLE circuits 
        ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE NOT NULL;
        """,
        """
        ALTER TABLE circuits 
        ADD COLUMN IF NOT EXISTS share_slug VARCHAR(255);
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_circuits_share_slug ON circuits(share_slug);
        """
    ]

    with sync_engine.begin() as conn:
        print("Starting Phase 4 table database migrations...")
        for q in table_queries:
            try:
                conn.execute(text(q))
                print(f"Executed query successfully: {q.strip()[:60]}...")
            except Exception as e:
                print(f"Error executing query {q.strip()[:60]}...: {e}")
        print("Phase 4 migrations finished.")

if __name__ == "__main__":
    run_migrations()
