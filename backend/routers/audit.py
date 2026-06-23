"""
QuantCAI Enterprise — Audit Log API Router
============================================
Provides read-only access to immutable audit logs for compliance administrators.
Supports filtering, pagination, and CSV/JSON export.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core.database import get_db
from security import get_current_user
import models as DBmodels

logger = logging.getLogger("quantcai.routers.audit")

router = APIRouter(prefix="/api/v1/audit", tags=["audit-logs"])


class AuditLogEntry(BaseModel):
    id: int
    userId: Optional[int] = None
    action: str
    tableName: str
    recordId: int
    oldValue: Optional[dict] = None
    newValue: Optional[dict] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    timestamp: Optional[str] = None


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="Paginated, filterable audit logs. Requires admin role.",
)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """List audit logs with optional filters. Requires admin or root role."""
    # RBAC check: only admins and root can view audit logs
    if current_user.role not in (DBmodels.UserRole.ADMIN, DBmodels.UserRole.ROOT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit log access requires admin or root role.",
        )

    from services.audit import get_audit_logs, get_audit_log_count

    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        table_name=table_name,
        limit=limit,
        offset=offset,
    )

    total = await get_audit_log_count(
        db=db,
        user_id=user_id,
        action=action,
        table_name=table_name,
    )

    return AuditLogListResponse(
        logs=[AuditLogEntry(**log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/logs/export",
    summary="Export audit logs as JSON",
    description="Export filtered audit logs for compliance reporting.",
)
async def export_audit_logs(
    action: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """Export audit logs as JSON for compliance. Requires admin role."""
    if current_user.role not in (DBmodels.UserRole.ADMIN, DBmodels.UserRole.ROOT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit log export requires admin or root role.",
        )

    from services.audit import get_audit_logs

    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        table_name=table_name,
        limit=limit,
        offset=0,
    )

    import json
    content = json.dumps({"audit_logs": logs, "total": len(logs)}, indent=2, default=str)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=quantcai_audit_logs.json"
        },
    )
