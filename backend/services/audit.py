"""
QuantCAI Enterprise — Immutable Audit Logging Service
======================================================
Write-only audit records for enterprise compliance (SOC 2, ISO 27001).
No UPDATE or DELETE operations are exposed — immutability is enforced.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

import models as DBmodels

logger = logging.getLogger("quantcai.audit")


async def log_event(
    db: AsyncSession,
    action: str,
    table_name: str,
    record_id: int,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> DBmodels.AuditLog:
    """
    Create an immutable audit log entry.
    
    This function only INSERTS — no update or delete is ever performed
    on audit records, ensuring compliance with SOC 2 immutability requirements.
    """
    audit = DBmodels.AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit)
    await db.flush()

    logger.info(
        f"Audit: {action} on {table_name}#{record_id} "
        f"by user={user_id} from {ip_address}"
    )
    return audit


async def log_auth_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> DBmodels.AuditLog:
    """Log authentication events (login, logout, SSO, failed attempts)."""
    return await log_event(
        db=db,
        action=action,
        table_name="auth",
        record_id=user_id or 0,
        user_id=user_id,
        user_email=user_email,
        new_value=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_job_event(
    db: AsyncSession,
    action: str,
    job_id: str,
    user_id: int,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> DBmodels.AuditLog:
    """Log quantum job execution events."""
    return await log_event(
        db=db,
        action=action,
        table_name="quantum_jobs",
        record_id=0,  # Use metadata for job_id since it's a string
        user_id=user_id,
        new_value={"job_id": job_id, **(metadata or {})},
        ip_address=ip_address,
    )


async def log_security_event(
    db: AsyncSession,
    action: str,
    user_id: int,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> DBmodels.AuditLog:
    """Log security configuration changes (SSO, API keys, RBAC)."""
    return await log_event(
        db=db,
        action=action,
        table_name="security_config",
        record_id=user_id,
        user_id=user_id,
        new_value=metadata,
        ip_address=ip_address,
    )


async def log_billing_event(
    db: AsyncSession,
    action: str,
    user_id: int,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> DBmodels.AuditLog:
    """Log billing and budget events."""
    return await log_event(
        db=db,
        action=action,
        table_name="billing",
        record_id=user_id,
        user_id=user_id,
        new_value=metadata,
        ip_address=ip_address,
    )


async def get_audit_logs(
    db: AsyncSession,
    org_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Query audit logs with filters. Returns results in reverse chronological order.
    """
    stmt = select(DBmodels.AuditLog).order_by(desc(DBmodels.AuditLog.created_at))

    if user_id is not None:
        stmt = stmt.where(DBmodels.AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(DBmodels.AuditLog.action == action)
    if table_name is not None:
        stmt = stmt.where(DBmodels.AuditLog.table_name == table_name)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "userId": log.user_id,
            "action": log.action,
            "tableName": log.table_name,
            "recordId": log.record_id,
            "oldValue": log.old_value,
            "newValue": log.new_value,
            "ipAddress": log.ip_address,
            "userAgent": log.user_agent,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


async def get_audit_log_count(
    db: AsyncSession,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
) -> int:
    """Get total count of audit logs matching filters."""
    stmt = select(func.count(DBmodels.AuditLog.id))

    if user_id is not None:
        stmt = stmt.where(DBmodels.AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(DBmodels.AuditLog.action == action)
    if table_name is not None:
        stmt = stmt.where(DBmodels.AuditLog.table_name == table_name)

    result = await db.execute(stmt)
    return result.scalar_one()
