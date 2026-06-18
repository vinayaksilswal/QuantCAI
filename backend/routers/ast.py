import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import models as DBmodels
from core.database import get_db
from core.auth import get_current_user
from security import get_subscription_plan
from services.ast_scanner import ASTScanner

logger = logging.getLogger("quantcai.ast_router")
router = APIRouter(prefix="/api/v1/ast", tags=["AST Scanner"])

class ScanCodeRequest(BaseModel):
    filename: str
    content: str
    language: str

@router.post("/scan-file")
async def scan_single_file(
    body: ScanCodeRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Scan a single code file for post-quantum cryptographic safety.
    """
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    if plan.lower() not in ("pro", "enterprise", "api_metered", "institutional"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AST scanning is an Enterprise/Pro level feature. Please upgrade your plan."
        )

    try:
        findings = ASTScanner.scan_code(body.filename, body.content, body.language)
        
        # Log usage
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.PQC_SCAN,
            credits_used=1,
            metadata_={"filename": body.filename, "type": "ast_file"}
        )
        db.add(usage_event)
        await db.commit()
        
        return {
            "filename": body.filename,
            "language": body.language,
            "vulnerabilities": findings,
            "total_findings": len(findings)
        }
    except Exception as e:
        logger.error(f"Error scanning code file {body.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code scan failed: {str(e)}")


@router.post("/scan-zip")
async def scan_zip_archive(
    file: UploadFile = File(...),
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Scan a ZIP archive containing multiple codebase source files.
    """
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    if plan.lower() not in ("pro", "enterprise", "api_metered", "institutional"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AST scanning is an Enterprise/Pro level feature. Please upgrade your plan."
        )

    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a ZIP archive."
        )

    try:
        zip_bytes = await file.read()
        
        # Limit total ZIP file size to 50MB to prevent server overload
        if len(zip_bytes) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded archive exceeds 50MB limit."
            )
            
        report = ASTScanner.scan_zip_bytes(zip_bytes)
        
        # Log usage
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.PQC_SCAN,
            credits_used=5, # Multiple files scan uses 5 credits
            metadata_={"archive_name": file.filename, "type": "ast_zip"}
        )
        db.add(usage_event)
        await db.commit()
        
        return report
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error scanning zip archive {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Archive scan failed: {str(e)}")


class RefactorRequest(BaseModel):
    filename: str
    content: str
    line_no: int
    issue_title: str


@router.post("/refactor")
async def refactor_code_vulnerability(
    body: RefactorRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an AI patch using Gemini to resolve a specific AST vulnerability.
    """
    plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
    if plan.lower() not in ("pro", "enterprise", "api_metered", "institutional"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI code remediation is a Pro/Enterprise level feature. Please upgrade your plan."
        )

    try:
        patch = ASTScanner.generate_code_remediation(
            filename=body.filename,
            file_content=body.content,
            line_no=body.line_no,
            issue_title=body.issue_title
        )
        return {"patch": patch}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to generate refactoring patch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refactoring failed: {str(e)}")

