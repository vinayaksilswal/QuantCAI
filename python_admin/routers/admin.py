"""
=============================================================================
QuantCAI — Admin Dashboard Router
=============================================================================
Serves the admin dashboard HTML page with platform statistics.
Uses request.app.state.prisma for all database operations.
All endpoints are authenticated via JWT cookie/Bearer token.
=============================================================================
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth import verify_credentials

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_credentials)],
)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> Any:
    """
    Main admin dashboard page.

    Renders the dashboard template with:
    - Campaign statistics
    - Social and Email automation statistics
    - Full campaign catalog
    """
    prisma = request.app.state.prisma

    # Aggregate statistics
    campaigns_count = await prisma.socialcampaign.count()
    social_posts_count = await prisma.socialpost.count()
    email_campaigns_count = await prisma.emailcampaign.count()

    # All campaigns for the management tab
    campaigns_db = await prisma.socialcampaign.find_many(
        order=[
            {"createdAt": "desc"},
        ]
    )

    # Convert to dicts for Jinja2 template rendering
    campaigns = [c.model_dump() for c in campaigns_db]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Admin Dashboard",
            "campaigns_count": campaigns_count,
            "social_posts_count": social_posts_count,
            "email_campaigns_count": email_campaigns_count,
            "campaigns": campaigns,
        },
    )
