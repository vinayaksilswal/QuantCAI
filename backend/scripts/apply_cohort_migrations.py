import os
import sys
from sqlalchemy import text

# Add the parent directory to Python path to import core config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import sync_engine

def run_migrations():
    queries = [
        # 1. Add columns to courses table if they don't exist
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS capacity INTEGER;",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS enrollment_status VARCHAR(50) DEFAULT 'open' NOT NULL;",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS zoom_link VARCHAR(500);",
        
        # 2. Create cohort_enrollments table
        """
        CREATE TABLE IF NOT EXISTS cohort_enrollments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            payment_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
            payment_id VARCHAR(255),
            enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
            CONSTRAINT uq_user_cohort_enrollment UNIQUE (user_id, course_id)
        );
        """,
        # Indexes
        "CREATE INDEX IF NOT EXISTS ix_cohort_enrollments_user_id ON cohort_enrollments(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_cohort_enrollments_course_id ON cohort_enrollments(course_id);",

        # 3. Seed default cohort course if none exists
        """
        INSERT INTO courses (id, title, description, is_active, start_date, end_date, capacity, enrollment_status, zoom_link)
        VALUES (
            1, 
            'Applied Quantum Software Engineering', 
            'An 8-week intensive program designed for software engineers transitioning to quantum computing and PQC security frameworks. Master Shor''s algorithm, VQE, and CBOM compliance.', 
            true, 
            '2026-08-01 09:00:00+00', 
            '2026-09-26 17:00:00+00', 
            20, 
            'open', 
            'https://zoom.us/j/9876543210'
        )
        ON CONFLICT (id) DO NOTHING;
        """
    ]
    
    with sync_engine.begin() as conn:
        print("Starting cohort database migrations...")
        for q in queries:
            try:
                conn.execute(text(q))
                print(f"Executed query successfully: {q.strip()[:60]}...")
            except Exception as e:
                print(f"Error executing query {q.strip()[:60]}...: {e}")
        print("Migrations finished.")

if __name__ == "__main__":
    run_migrations()
