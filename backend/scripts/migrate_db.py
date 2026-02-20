"""
Database migration script to add missing columns to existing tables
"""
import database as db
import DBmodels
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add missing columns to existing tables"""
    try:
        with db.engine.connect() as connection:
            # Check if created_at column exists in users table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='created_at'
            """))
            
            if result.fetchone() is None:
                logger.info("Adding created_at and updated_at columns to users table...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                """))
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                """))
                connection.commit()
                logger.info("✓ Successfully added created_at and updated_at to users table")
            else:
                logger.info("✓ created_at column already exists in users table")

            # Ensure token_version column exists in users table
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='token_version'
            """))

            if result.fetchone() is None:
                logger.info("Adding token_version column to users table for token revocation...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN token_version INTEGER DEFAULT 0 NOT NULL
                """))
                connection.commit()
                logger.info("✓ Successfully added token_version to users table")
            else:
                logger.info("✓ token_version column already exists in users table")
            
            # Check if logtable exists, if not create it
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='logtable'
            """))
            
            if result.fetchone() is None:
                logger.info("Creating logtable...")
                DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.Log.__table__])
                logger.info("✓ Successfully created logtable")
            else:
                logger.info("✓ logtable already exists")
            
            # Check if courses table exists
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='courses'
            """))
            
            if result.fetchone() is None:
                logger.info("Creating courses table...")
                DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.Course.__table__])
                logger.info("✓ Successfully created courses table")
            else:
                logger.info("✓ courses table already exists")

            # Ensure refresh_tokens table exists
            logger.info("Ensuring refresh_tokens table exists...")
            DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.RefreshToken.__table__])
            logger.info("✓ refresh_tokens table is present")

            # Check if circuits table exists
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='circuits'
            """))
            
            if result.fetchone() is None:
                logger.info("Creating circuits table...")
                DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.Circuit.__table__])
                logger.info("✓ Successfully created circuits table")
            else:
                logger.info("✓ circuits table already exists")

            # Account security: add columns to users
            # failed_login_attempts: INTEGER DEFAULT 0 NOT NULL
            # locked_until: TIMESTAMP NULL
            col_defs = {
                "email_verified": "BOOLEAN DEFAULT FALSE NOT NULL",
                "verification_sent_at": "TIMESTAMP NULL",
                "failed_login_attempts": "INTEGER DEFAULT 0 NOT NULL",
                "locked_until": "TIMESTAMP NULL"
            }
            for col, col_type in col_defs.items():
                result = connection.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{col}'
                """))
                if result.fetchone() is None:
                    logger.info(f"Adding {col} column to users table...")
                    connection.execute(text(f"""
                        ALTER TABLE users 
                        ADD COLUMN {col} {col_type}
                    """))
                    connection.commit()
                    logger.info(f"✓ Successfully added {col} to users table")
                else:
                    logger.info(f"✓ {col} column already exists")

            # Ensure email_verification_tokens table exists
            logger.info("Ensuring email_verification_tokens table exists...")
            DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.EmailVerificationToken.__table__])
            logger.info("✓ email_verification_tokens table is present")

            # Ensure notification_requests table exists
            logger.info("Ensuring notification_requests table exists...")
            DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.NotificationRequest.__table__])
            logger.info("✓ notification_requests table is present")

            # Ensure subscribers table exists
            logger.info("Ensuring subscribers table exists...")
            DBmodels.Base.metadata.create_all(bind=db.engine, tables=[DBmodels.Subscriber.__table__])
            logger.info("✓ subscribers table is present")

        # ======================
        # Performance Indexes
        # ======================
        # These indexes improve query performance for common lookups.
        # Use CONCURRENTLY to avoid locking production DB (PostgreSQL 12+).
        index_definitions = [
            ("ix_posts_author_id", "posts(author_id)"),
            ("ix_posts_created_at", "posts(created_at DESC)"),
            ("ix_posts_author_created", "posts(author_id, created_at DESC)"),
            ("ix_comments_post_id", "comments(post_id)"),
            ("ix_comments_author_id", "comments(author_id)"),
            ("ix_comments_created_at", "comments(created_at DESC)"),
            ("ix_circuits_user_id", "circuits(user_id)"),
            ("ix_refresh_tokens_user_id", "refresh_tokens(user_id)"),
            ("ix_email_verification_tokens_user_id", "email_verification_tokens(user_id)"),
        ]

        # Need a new connection with autocommit for CREATE INDEX CONCURRENTLY
        with db.engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            for idx_name, table_columns in index_definitions:
                # Check if index exists in PostgreSQL
                result = conn.execute(text("""
                    SELECT 1 FROM pg_indexes WHERE indexname = :idx
                """), {"idx": idx_name}).fetchone()
                if result is None:
                    logger.info(f"Creating index {idx_name} on {table_columns}...")
                    try:
                        conn.execute(text(f"CREATE INDEX CONCURRENTLY {idx_name} ON {table_columns}"))
                        logger.info(f"✓ Created index {idx_name}")
                    except Exception as e:
                        # Fallback to non-concurrent if CONCURRENTLY fails (e.g., older PG version, or already running within transaction)
                        logger.warning(f"CONCURRENTLY failed for {idx_name}: {e}. Trying normal CREATE INDEX.")
                        try:
                            conn.execute(text(f"CREATE INDEX {idx_name} ON {table_columns}"))
                            logger.info(f"✓ Created index {idx_name} (non-concurrent)")
                        except Exception as e2:
                            logger.error(f"Failed to create index {idx_name}: {e2}")
                else:
                    logger.info(f"✓ Index {idx_name} already exists")

        logger.info("✓ Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting database migration...")
    migrate_database()

