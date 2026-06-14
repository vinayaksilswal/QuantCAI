from typing import Optional
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
from services.pqc_scanner import scan_domain_async, generate_cyclonedx_cbom
from schemas_pqc import ScanRequest, ScanResponse
import scanner_engine
import asyncio


router = APIRouter(prefix="/api/v1", tags=["pqc-scanner"])
logger = logging.getLogger("quantcai.pqc_router")

@router.get("/scan/{domain}")
async def perform_pqc_scan(
    domain: str,
    request: Request,
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
            res = json.loads(cached_result)
            tier = getattr(request.state, "tier", "FREE")
            if tier == "FREE" and "certificates" in res:
                res["certificates"] = [c for c in res["certificates"] if c.get("index") == 0]
                if "findings" in res:
                    res["findings"] = [f for f in res["findings"] if "Intermediate CA" not in f.get("title", "")]
            return res
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
        
        tier = getattr(request.state, "tier", "FREE")
        if tier == "FREE" and "certificates" in result:
            result["certificates"] = [c for c in result["certificates"] if c.get("index") == 0]
            if "findings" in result:
                result["findings"] = [f for f in result["findings"] if "Intermediate CA" not in f.get("title", "")]
        return result
    except Exception as e:
        logger.error(f"Error performing PQC scan on domain {domain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/enterprise/scan/{domain}/cyclonedx")
async def perform_enterprise_pqc_scan_cyclonedx(
    domain: str,
    port: Optional[int] = None,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform TLS scan on the specified domain for PQC vulnerabilities and return CycloneDX 1.6 CBOM.
    Exclusively for the Enterprise tier.
    """
    domain = domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="Domain name is required")
        
    # Check subscription and roles
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    is_enterprise = plan.lower() == "enterprise" or current_user.role in (DBmodels.UserRole.ROOT, DBmodels.UserRole.ENTERPRISE_USER)
    
    if not is_enterprise:
        raise HTTPException(
            status_code=403, 
            detail="Access restricted. Enterprise tier subscription or role required."
        )
        
    logger.info(f"Enterprise CycloneDX PQC Scan request received for domain: {domain} (port: {port}) by user {current_user.email}")
    
    cache_key = f"pqc_scan_cdx:{domain}:{port}"
    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached CycloneDX PQC scan result for domain: {domain}")
            return json.loads(cached_result)
    except Exception as e:
        logger.error(f"Failed to read from Redis cache for domain {domain}: {e}", exc_info=True)
        
    try:
        # Perform scan (scan_domain_async will handle internal/custom ports)
        result = await scan_domain_async(domain, port)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=f"Scan failed: {result['error']['message']}")
            
        # Format as CycloneDX 1.6 CBOM
        cdx_cbom = generate_cyclonedx_cbom(result)
        
        # Log usage
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.PQC_SCAN,
            credits_used=1,
            metadata_={"domain": domain, "port": port, "format": "cyclonedx"}
        )
        db.add(usage_event)
        await db.commit()
        
        try:
            await redis_client.setex(cache_key, 86400, json.dumps(cdx_cbom))
        except Exception as e:
            logger.error(f"Failed to write to Redis cache for domain {domain}: {e}", exc_info=True)
        
        return cdx_cbom
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing Enterprise PQC scan on domain {domain}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/pqc/scan", response_model=ScanResponse)
async def perform_pro_pqc_scan(
    payload: ScanRequest,
    request: Request,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform a complete, enterprise-grade PQC vulnerability scan for the target domain and port.
    """
    domain = payload.domain.strip()
    port = payload.port
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
            
    logger.info(f"Pro PQC Scan request received for domain: {domain}:{port} by user {current_user.email}")
    
    cache_key = f"pqc_scan_pro:{domain}:{port}"
    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached Pro PQC scan result for domain: {domain}:{port}")
            res = json.loads(cached_result)
            tier = getattr(request.state, "tier", "FREE")
            if tier == "FREE" and "certificates" in res:
                res["certificates"] = [c for c in res["certificates"] if c.get("index") == 0]
                if "findings" in res:
                    res["findings"] = [f for f in res["findings"] if "Intermediate CA" not in f.get("title", "")]
            return res
    except Exception as e:
        logger.error(f"Failed to read from Redis cache for domain {domain}:{port}: {e}", exc_info=True)
        
    try:
        # Execute blocking socket scan in worker thread to prevent blocking event loop
        result = await asyncio.to_thread(scanner_engine.scan_tls_pqc, domain, port)
        
        # Log usage
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.PQC_SCAN,
            credits_used=1,
            metadata_={"domain": domain, "port": port}
        )
        db.add(usage_event)
        await db.commit()
        
        try:
            await redis_client.setex(cache_key, 86400, json.dumps(result))
        except Exception as e:
            logger.error(f"Failed to write to Redis cache for domain {domain}:{port}: {e}", exc_info=True)
        
        tier = getattr(request.state, "tier", "FREE")
        if tier == "FREE" and "certificates" in result:
            result["certificates"] = [c for c in result["certificates"] if c.get("index") == 0]
            if "findings" in result:
                result["findings"] = [f for f in result["findings"] if "Intermediate CA" not in f.get("title", "")]
        return result
    except ConnectionError as ce:
        logger.error(f"Connection error scanning {domain}:{port}: {ce}")
        raise HTTPException(status_code=502, detail=str(ce))
    except Exception as e:
        logger.error(f"Error performing Pro PQC scan on domain {domain}:{port}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


