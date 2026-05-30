import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import models as DBmodels
from core.database import get_db
from core.auth import get_current_user
from security import get_subscription_plan, redis_client
from services.pqc_scanner import scan_domain_async

router = APIRouter(prefix="/api/v1", tags=["pqc-scanner"])
logger = logging.getLogger("quantcai.pqc_router")

@router.get("/scan/{domain}")
async def perform_pqc_scan(
    domain: str,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform TLS scan on the specified domain for PQC vulnerabilities.
    """
    domain = domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="Domain name is required")
        
    # Check subscription and limits
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    is_pro = plan.lower() in ("pro", "enterprise")
    
    if not is_pro:
        # Free tier: enforce daily limit of 5 scans
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        stmt = select(func.count(DBmodels.UsageEvent.id)).where(
            DBmodels.UsageEvent.user_id == current_user.id,
            DBmodels.UsageEvent.event_type == DBmodels.UsageEventType.PQC_SCAN,
            DBmodels.UsageEvent.created_at >= today_start
        )
        result = await db.execute(stmt)
        scans_today = result.scalar() or 0
        if scans_today >= 5:
            raise HTTPException(
                status_code=403, 
                detail="Free tier limit of 5 PQC scans per day reached. Upgrade to Pro for unlimited scans."
            )
            
    logger.info(f"PQC Scan request received for domain: {domain} by user {current_user.email}")
    
    cache_key = f"pqc_scan:{domain}"
    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached PQC scan result for domain: {domain}")
            return json.loads(cached_result)
    except Exception as e:
        logger.error(f"Failed to read from Redis cache for domain {domain}: {e}", exc_info=True)
        
    try:
        result = await scan_domain_async(domain)
        
        # Log usage
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.PQC_SCAN,
            credits_used=1,
            metadata_={"domain": domain}
        )
        db.add(usage_event)
        await db.commit()
        
        try:
            await redis_client.setex(cache_key, 86400, json.dumps(result))
        except Exception as e:
            logger.error(f"Failed to write to Redis cache for domain {domain}: {e}", exc_info=True)
        
        return result
    except Exception as e:
        logger.error(f"Error performing PQC scan on domain {domain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
