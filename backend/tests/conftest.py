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

@pytest.fixture(autouse=True, scope="function")
def mock_redis():
    """Mock Redis client globally using fakeredis."""
    try:
        import fakeredis.aioredis
    except ImportError:
        pytest.skip("fakeredis is required to run tests with Redis mocks")
        
    server = fakeredis.FakeServer()
    mock_redis_client = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
    
    with patch("security.redis_client", mock_redis_client):
        yield mock_redis_client

@pytest_asyncio.fixture
async def free_user(cleanup_database_connections):
    """Fixture for a free tier user."""
    from models import User
    from core.database import async_session_factory
    
    async with async_session_factory() as session:
        user = User(
            email="free@example.com",
            name="Free User",
            password_hash="fakehash",
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
            password_hash="fakehash",
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
            password_hash="fakehash",
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
