"""
=============================================================================
QuantCAI — Resend Email Client
=============================================================================
Handles transactional and marketing email delivery via the Resend SDK.
Replaces the previous SMTP-based email service with Resend's modern API.

Sender: support@quantcai.in (configured via settings)

Prerequisites:
  1. Resend account with API key (set RESEND_API_KEY in env)
  2. DNS domain verification for quantcai.in (MX, SPF, DKIM records)
     See: https://resend.com/docs/dashboard/domains/introduction

Key Functions:
  - send_email_blast(): Batch send a promotional email to all Audience
    members, chunked to avoid rate limits.
  - send_single_email(): Send a single email to one recipient.
=============================================================================
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from prisma import Prisma
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings

# =============================================================================
# Resend SDK Import — with graceful fallback
# =============================================================================
try:
    import resend
except ImportError:
    resend = None  # type: ignore[assignment]
    logger.warning(
        "Resend SDK not installed. Email sending disabled. "
        "Install with: pip install resend"
    )

# Batch size for email sends (Resend rate limit: ~10 emails/second on free tier)
EMAIL_BATCH_SIZE = 50

# Delay between batches (seconds) to respect rate limits
BATCH_DELAY_SECONDS = 2


# =============================================================================
# Resend Initialization
# =============================================================================
def _init_resend() -> bool:
    """
    Initialize the Resend SDK with the API key from settings.
    Must be called before any send operations.

    Returns:
        True if Resend is properly configured, False otherwise
    """
    if resend is None:
        logger.error("Resend SDK not available — install with: pip install resend")
        return False

    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — email sending disabled")
        return False

    resend.api_key = settings.resend_api_key
    return True


# =============================================================================
# Single Email Send
# =============================================================================
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(
        f"Resend retry attempt {retry_state.attempt_number}"
    ),
)
async def send_single_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict[str, Any]:
    """
    Send a single email via Resend.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Optional plain text fallback body

    Returns:
        Dict with 'success' bool and 'id' (Resend email ID) or 'error'
    """
    if not _init_resend():
        return {"success": False, "error": "Resend not configured"}

    try:
        params: dict[str, Any] = {
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            params["text"] = text_body

        email_response = resend.Emails.send(params)

        email_id = (
            email_response.get("id", "")
            if isinstance(email_response, dict)
            else getattr(email_response, "id", "")
        )
        logger.info(f"✓ Email sent to {to_email}: {email_id}")
        return {"success": True, "id": email_id}

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise  # Let tenacity handle retry


# =============================================================================
# Batch Email Blast
# =============================================================================
async def send_email_blast(
    subject: str,
    html_body: str,
    text_body: str = "",
    *,
    prisma: Prisma | None = None,
) -> dict[str, Any]:
    """
    Send a promotional email to all audience members and users.

    Queries the Audience and User tables, deduplicates emails, and sends
    in batches to respect Resend's rate limits.

    Args:
        subject: Email subject line
        html_body: HTML email body content
        text_body: Plain text fallback body
        prisma: Prisma client instance (required for database queries)

    Returns:
        Dict with 'success' bool, 'count' (emails sent), and optional 'error'
    """
    if not _init_resend():
        logger.warning(f"Resend not configured. Simulating email blast: {subject}")
        return {"success": True, "count": 0, "error": "Resend not configured (simulated)"}

    if not prisma:
        logger.error("Prisma client required for email blast")
        return {"success": False, "count": 0, "error": "No database connection"}

    try:
        # Gather all recipients who haven't unsubscribed
        audiences = await prisma.audience.find_many(where={"unsubscribed": False})

        # Deduplicate email addresses (case-insensitive)
        email_set: set[str] = set()
        for a in audiences:
            email_set.add(a.email.lower().strip())

        emails = list(email_set)

        if not emails:
            logger.info("No recipients found for email blast")
            return {"success": True, "count": 0}

        logger.info(
            f"Sending email blast to {len(emails)} recipients | "
            f"Subject: {subject}"
        )

        # Send in batches to respect rate limits
        sent_count = 0
        errors: list[str] = []

        for i in range(0, len(emails), EMAIL_BATCH_SIZE):
            batch = emails[i : i + EMAIL_BATCH_SIZE]

            for email_addr in batch:
                try:
                    params: dict[str, Any] = {
                        "from": settings.resend_from_email,
                        "to": [email_addr],
                        "subject": subject,
                        "html": html_body,
                    }
                    if text_body:
                        params["text"] = text_body

                    resend.Emails.send(params)
                    sent_count += 1
                except Exception as e:
                    error_msg = f"{email_addr}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(f"Failed to send to {email_addr}: {e}")

            # Delay between batches to avoid rate limiting
            if i + EMAIL_BATCH_SIZE < len(emails):
                import asyncio
                await asyncio.sleep(BATCH_DELAY_SECONDS)

        logger.info(
            f"✓ Email blast complete: {sent_count}/{len(emails)} sent "
            f"({len(errors)} failures)"
        )

        return {
            "success": sent_count > 0,
            "count": sent_count,
            "total_recipients": len(emails),
            "errors": errors[:10] if errors else None,  # Limit error list
        }

    except Exception as e:
        logger.error(f"Email blast failed: {e}")
        return {"success": False, "count": 0, "error": str(e)}
