import logging
from typing import AsyncGenerator, Tuple, Dict, Any
from urllib.parse import urlparse, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core.config import settings

logger = logging.getLogger(__name__)

def _get_async_database_config() -> Tuple[str, Dict[str, Any]]:
    """
    Reads DATABASE_URL from settings and formats it for async driver compatibility.
    Strips query arguments (like sslmode, channel_binding) which trigger errors in asyncpg,
    and maps them to connection arguments instead.
    """
    url = settings.DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it to point to your PostgreSQL database."
        )
    
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    connect_args = {}
    
    # Handle SQLite fallback
    if "sqlite" in scheme:
        # aiosqlite is the standard async sqlite driver
        if "sqlite+aiosqlite://" not in url:
            clean_url = url.replace("sqlite://", "sqlite+aiosqlite://")
        else:
            clean_url = url
        return clean_url, connect_args

    # Check for SSL settings in connection query string
    query_params = parsed.query.lower()
    if "sslmode=require" in query_params or "ssl=true" in query_params or "sslmode=prefer" in query_params:
        # Standard configuration for secure database connections (e.g. Neon, AWS RDS)
        connect_args["ssl"] = True

    # Rebuild standard PostgreSQL connection URL with the asyncpg driver prefix
    clean_url = urlunparse(("postgresql+asyncpg", parsed.netloc, parsed.path, "", "", ""))
    return clean_url, connect_args


DATABASE_URL, connect_args = _get_async_database_config()

# Connection pooling options
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,  # Verify connection health before emitting queries
    "connect_args": connect_args
}

# Apply connection pooling options for PostgreSQL (asyncpg)
if "sqlite" not in DATABASE_URL:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create the async engine
engine = create_async_engine(
    DATABASE_URL,
    **engine_kwargs
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# FastAPI database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional async database session."""
    async with async_session_factory() as db:
        try:
            yield db
        finally:
            await db.close()

# Sync compatibility layer for sync routers and scripts
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
sync_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
