import logging
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session_factory
from core.auth import get_current_user
import models as DBmodels

logger = logging.getLogger(__name__)

async def get_db_session(
    current_user: DBmodels.User = Depends(get_current_user)
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession with session-local
    RLS context variables set for the authenticated user and their organization.
    Ensures full multi-tenant isolation at the database level.
    """
    async with async_session_factory() as session:
        try:
            # Switch to app_user role so that RLS is enforced (avoiding superuser/owner bypass)
            await session.execute(text("SET ROLE app_user"))
            
            # We must execute SET LOCAL commands within a transaction block for them to take effect.
            # SET LOCAL changes are scoped to the current transaction.
            await session.execute(text(f"SET LOCAL app.user_id = '{current_user.id}'"))
            
            if getattr(current_user, "org_id", None) is not None:
                await session.execute(text(f"SET LOCAL app.org_id = '{current_user.org_id}'"))
            
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Error in RLS db session, rolling back: {str(e)}", exc_info=True)
            await session.rollback()
            raise e
        finally:
            # Reset role back to connection owner before returning to pool
            try:
                await session.execute(text("RESET ROLE"))
                await session.commit()
            except Exception:
                pass
            await session.close()
