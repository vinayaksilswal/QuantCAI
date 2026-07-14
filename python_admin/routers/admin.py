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
    - Order count and total revenue
    - Product count
    - Recent orders (last 10)
    - Full product catalog (for the catalog tab)
    """
    prisma = request.app.state.prisma

    # Aggregate statistics
    orders_count = await prisma.order.count()
    products_count = await prisma.product.count()

    # Total revenue via raw SQL (Prisma Python doesn't support aggregate yet)
    revenue_result = await prisma.query_raw(
        'SELECT COALESCE(SUM("totalAmount"), 0) as total FROM "Order"'
    )
    total_revenue = revenue_result[0]["total"] if revenue_result else 0

    # Recent orders for the dashboard table
    recent_orders = await prisma.order.find_many(
        order={"createdAt": "desc"},
        take=10,
    )

    # All products for the catalog management tab
    products_db = await prisma.product.find_many(
        order=[
            {"manualSortOrder": "asc"},
            {"listCount": "desc"},
        ]
    )

    # Convert to dicts for Jinja2 template rendering
    products = [p.model_dump() for p in products_db]
    orders = [order.model_dump() for order in recent_orders]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Admin Dashboard",
            "orders_count": orders_count,
            "products_count": products_count,
            "total_revenue": total_revenue,
            "orders": orders,
            "products": products,
        },
    )
