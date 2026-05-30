import os
import sys
import pytest_asyncio

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
