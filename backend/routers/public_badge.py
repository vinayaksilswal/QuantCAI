from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from core.database import get_db
import models as DBmodels

router = APIRouter(prefix="/api/v1/public", tags=["Public Badges"])
logger = logging.getLogger("quantcai.routers.public_badge")

def generate_svg(text: str, bg_color: str) -> str:
    """
    Helper to render a clean, high-fidelity SVG badge.
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="20" viewBox="0 0 180 20">
  <linearGradient id="g" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="180" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="110" height="20" fill="#2d3748"/>
    <rect x="110" width="70" height="20" fill="{bg_color}"/>
    <rect width="180" height="20" fill="url(#g)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="110">
    <text x="560" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="900">PQC Readiness</text>
    <text x="560" y="140" transform="scale(.1)" textLength="900">PQC Readiness</text>
    <text x="1450" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="500">{text}</text>
    <text x="1450" y="140" transform="scale(.1)" textLength="500">{text}</text>
  </g>
</svg>'''

# Single braces. The doubled form registered a literal path segment named
# "{target_id}" rather than a path parameter, so every real badge request 404'd
# and the public badge — an inbound-link driver that points back at the
# platform from customers' own sites — never worked at all.
@router.get("/badge/{target_id}")
async def get_target_badge(
    target_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a dynamic PQC compliance badge SVG for a given target ID.
    Unauthenticated public endpoint. Returns fallback grade if target is invalid/unscanned.
    """
    bg_color = "#64748b" # default slate
    text_val = "N/A"
    
    try:
        stmt = select(DBmodels.MonitoredTarget).where(DBmodels.MonitoredTarget.id == target_id)
        res = await db.execute(stmt)
        target = res.scalar_one_or_none()
        
        if target and target.last_scan_score is not None:
            score = target.last_scan_score
            if score >= 90:
                bg_color = "#10b981" # Emerald
                grade = "A"
            elif score >= 80:
                bg_color = "#3b82f6" # Blue
                grade = "B"
            elif score >= 70:
                bg_color = "#f59e0b" # Amber
                grade = "C"
            elif score >= 60:
                bg_color = "#ea580c" # Orange
                grade = "D"
            else:
                bg_color = "#ef4444" # Red
                grade = "F"
            text_val = f"{grade} ({int(score)}%)"
        elif target:
            text_val = "Pending"
            bg_color = "#4a5568"
    except Exception as e:
        logger.error(f"Error generating badge for target {target_id}: {e}", exc_info=True)
        # return fallback SVG directly instead of throwing 500 error to keep external UI intact

    svg_content = generate_svg(text_val, bg_color)
    
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
