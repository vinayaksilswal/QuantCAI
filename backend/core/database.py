import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

def _get_database_url() -> str:
    """Read DATABASE_URL from environment and fail fast if missing."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it to your production database connection string."
        )
    return url


DATABASE_URL = _get_database_url()

# Create engine with connection pooling
# In production, we typically don't use NullPool unless usage is very intermittent (like Lambda).
# For a persistent server, default pooling is better.

engine_kwargs = {
    "echo": False,
    # pool_pre_ping=True helps verify connections before usage, good for production stability
    "pool_pre_ping": True,
}

# SQLite memory db does not support pool_size and max_overflow
if "sqlite" not in DATABASE_URL:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Alias for backward compatibility
session = SessionLocal
