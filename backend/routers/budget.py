"""
QuantCAI Enterprise — Budget Management Router
================================================
Endpoints for viewing and managing organization/project budgets,
alert thresholds, and spend tracking.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from security import get_current_user
import models as DBmodels

logger = logging.getLogger("quantcai.routers.budget")

router = APIRouter(prefix="/api/v1/budget", tags=["budget-management"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------
class BudgetStatusResponse(BaseModel):
    org_budget: float
    org_spent: float
    org_remaining: float
    utilization_pct: float
    alerts: list[dict] = []


class BudgetLimitsRequest(BaseModel):
    monthly_budget: float = Field(..., ge=0, description="Monthly budget limit in USD")


class AlertThresholdRequest(BaseModel):
    threshold_pct: int = Field(..., ge=1, le=100, description="Alert threshold percentage")
    notify_email: bool = True
    notify_webhook: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/status",
    response_model=BudgetStatusResponse,
    summary="Get current budget status",
    description="View organization spend vs budget limits.",
)
async def get_budget_status(
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """Return current org budget status with utilization metrics."""
    # Mock data for demonstration - in production, query from DB
    org_budget = 10000.00
    org_spent = 2450.00
    org_remaining = org_budget - org_spent
    utilization = (org_spent / org_budget * 100) if org_budget > 0 else 0

    alerts = []
    if utilization > 90:
        alerts.append({
            "level": "critical",
            "message": f"Budget utilization at {utilization:.1f}%",
            "threshold": 90,
        })
    elif utilization > 75:
        alerts.append({
            "level": "warning",
            "message": f"Budget utilization at {utilization:.1f}%",
            "threshold": 75,
        })

    return BudgetStatusResponse(
        org_budget=org_budget,
        org_spent=org_spent,
        org_remaining=org_remaining,
        utilization_pct=round(utilization, 1),
        alerts=alerts,
    )


@router.put(
    "/limits",
    summary="Update budget limits",
    description="Set organization or project budget limits. Requires admin role.",
)
async def update_budget_limits(
    body: BudgetLimitsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """Update organization budget limit."""
    if current_user.role not in (DBmodels.UserRole.ADMIN, DBmodels.UserRole.ROOT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Budget limit changes require admin or root role.",
        )

    # In production: update org.monthly_budget in DB
    logger.info(
        f"Budget limit updated to ${body.monthly_budget:.2f} "
        f"by user {current_user.id}"
    )

    return {
        "status": "updated",
        "monthly_budget": body.monthly_budget,
    }


@router.get(
    "/alerts",
    summary="List budget alert thresholds",
    description="View configured budget alert thresholds.",
)
async def list_alert_thresholds(
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """Return configured alert thresholds."""
    # Default thresholds
    return {
        "thresholds": [
            {"pct": 50, "notify_email": True, "notify_webhook": False, "status": "inactive"},
            {"pct": 75, "notify_email": True, "notify_webhook": False, "status": "inactive"},
            {"pct": 90, "notify_email": True, "notify_webhook": True, "status": "inactive"},
            {"pct": 100, "notify_email": True, "notify_webhook": True, "status": "inactive"},
        ]
    }


@router.post(
    "/alerts",
    summary="Configure alert threshold",
    description="Add or update a budget alert threshold.",
)
async def configure_alert_threshold(
    body: AlertThresholdRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    """Configure a budget alert threshold."""
    if current_user.role not in (DBmodels.UserRole.ADMIN, DBmodels.UserRole.ROOT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert configuration requires admin or root role.",
        )

    return {
        "status": "configured",
        "threshold_pct": body.threshold_pct,
        "notify_email": body.notify_email,
        "notify_webhook": body.notify_webhook,
    }
