import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a safe, isolated database URL for testing BEFORE importing core.database.
# Use TEST_DATABASE_URL if defined, otherwise default to a local SQLite database file.
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
else:
    os.environ["DATABASE_URL"] = "sqlite:///test.db"

# core.config defaults ENVIRONMENT to "production", whose validator rejects the
# placeholder SECRET_KEY. Importing core.database therefore fails at collection
# time unless the caller happens to have exported the right variables, so set
# test-safe defaults here and keep the suite runnable with a bare `pytest`.
# setdefault, so a caller can still override any of these deliberately.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ENV", "test")
os.environ.setdefault(
    "SECRET_KEY", "test-only-secret-key-not-used-outside-the-test-suite-0123456789"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

from core.database import engine, sync_engine
from models import Base
from sqlalchemy import event

@event.listens_for(sync_engine, "before_cursor_execute", retval=True)
def before_cursor_execute_sync(conn, cursor, statement, parameters, context, executemany):
    if "TIMEZONE('utc', NOW())" in statement:
        statement = statement.replace("TIMEZONE('utc', NOW())", "CURRENT_TIMESTAMP")
    return statement, parameters

@event.listens_for(engine.sync_engine, "before_cursor_execute", retval=True)
def before_cursor_execute_async(conn, cursor, statement, parameters, context, executemany):
    if "TIMEZONE('utc', NOW())" in statement:
        statement = statement.replace("TIMEZONE('utc', NOW())", "CURRENT_TIMESTAMP")
    return statement, parameters

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

def pytest_sessionfinish(session, exitstatus):
    """Clean up local test.db sqlite file after test suite finishes."""
    try:
        if os.path.exists("test.db"):
            os.remove("test.db")
    except Exception:
        pass

@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup_database_connections():
    """
    Ensure the SQLAlchemy engine connection pool is disposed after each test.
    This prevents SSL/transport errors on event loop closure on Windows.
    """
    Base.metadata.create_all(bind=sync_engine)
        
    yield
    
    Base.metadata.drop_all(bind=sync_engine)
        
    await engine.dispose()

# Every module that does `from security import redis_client` binds its OWN
# module-level name at import time, so patching "security.redis_client" alone
# leaves all of them pointing at the real client — which then tries to reach
# localhost:6379 and fails. Patch each binding.
_REDIS_CLIENT_BINDINGS = (
    "security",
    "billing",
    "main",
    "metering_middleware",
    "middleware",
    "quantum_engine",
    "tier_limits",
    "tutor",
    "routers.developer",
    "routers.developer_api",
    "routers.entitlements",
    "routers.payment",
    "routers.paypal_billing",
    "routers.pqc",
    "routers.quantai",
)


@pytest.fixture(autouse=True, scope="function")
def mock_redis():
    """
    Mock Redis globally using fakeredis.

    fakeredis is a hard requirement declared in requirements-test.txt. It used
    to pytest.skip() when missing, which — because this fixture is autouse —
    silently skipped the ENTIRE suite while pytest still exited 0. CI reported
    success having run nothing at all.
    """
    import fakeredis.aioredis  # noqa: F401 - a missing dep must fail, not skip

    server = fakeredis.FakeServer()
    mock_redis_client = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)

    import importlib

    patches = []
    for module_name in _REDIS_CLIENT_BINDINGS:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        # Some modules import redis_client inside a function rather than at
        # module scope, so there is no attribute to replace. Patching those
        # raises AttributeError at start().
        if not hasattr(module, "redis_client"):
            continue
        patches.append(patch(f"{module_name}.redis_client", mock_redis_client))

    for p in patches:
        p.start()
    try:
        yield mock_redis_client
    finally:
        for p in patches:
            try:
                p.stop()
            except Exception:
                pass

@pytest_asyncio.fixture
async def free_user(cleanup_database_connections):
    """Fixture for a free tier user."""
    from models import User
    from core.database import async_session_factory
    
    async with async_session_factory() as session:
        user = User(
            email="free@example.com",
            name="Free User",
            hashed_password="fakehash",
            role="user",
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

@pytest_asyncio.fixture
async def pro_user(cleanup_database_connections):
    """Fixture for a pro tier user with an active subscription."""
    from models import User, Subscription
    from core.database import async_session_factory
    
    async with async_session_factory() as session:
        user = User(
            email="pro@example.com",
            name="Pro User",
            hashed_password="fakehash",
            role="user",
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.flush()
        
        sub = Subscription(
            user_id=user.id,
            plan="PRO",
            status="active",
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc)
        )
        session.add(sub)
        await session.commit()
        await session.refresh(user)
        return user

@pytest_asyncio.fixture
async def enterprise_user(cleanup_database_connections):
    """Fixture for an enterprise tier user with an active subscription."""
    from models import User, Subscription
    from core.database import async_session_factory
    
    async with async_session_factory() as session:
        user = User(
            email="enterprise@example.com",
            name="Enterprise User",
            hashed_password="fakehash",
            role="enterprise_user",
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.flush()
        
        sub = Subscription(
            user_id=user.id,
            plan="ENTERPRISE",
            status="active",
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc)
        )
        session.add(sub)
        await session.commit()
        await session.refresh(user)
        return user
