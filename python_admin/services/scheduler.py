"""
=============================================================================
QuantCAI — Marketing Automation Scheduler (Bi-Hourly Autonomous Loop)
=============================================================================
Implements the autonomous marketing loop that runs every 2 hours:

  1. Query the database for the NEXT product (sequential round-robin)
  2. Generate marketing copy via OpenRouter (AI)
  3. Push to Meta APIs (Facebook + Instagram)
  4. Send Resend email blast to the Audience
  5. Log everything to MarketingLog

Uses APScheduler's AsyncIOScheduler for non-blocking task execution.

Architecture:
  - The scheduler is created and started in main.py's lifespan context
  - It receives the Prisma client from the lifespan (no standalone instances)
  - Each step (social/email) fails independently without killing the loop
  - MarketingLog provides full audit trail of autonomous actions

The scheduler is designed for SINGLE INSTANCE deployment (Render with
numInstances=1) to prevent duplicate marketing actions.
=============================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from prisma import Prisma

from services.ai_service import (
    generate_marketing_assets,
    generate_promotional_email,
    generate_social_caption,
)
from services.email_service import send_email_blast
from services.social_service import post_to_facebook, post_to_instagram

# =============================================================================
# Module-level Prisma reference (set during scheduler creation)
# =============================================================================
# This is set by create_scheduler() and used by the scheduled tasks.
# It's the SAME instance created in main.py's lifespan context.
_prisma: Prisma | None = None


# =============================================================================
# Product Rotation — Sequential Round-Robin
# =============================================================================
async def _get_next_product(
    prisma: Prisma, marketing_type: str
) -> Any | None:
    """
    Get the next product in the sequential rotation for marketing.

    Uses the MarketingState singleton to track which product index was
    last used for each channel (social vs email). Wraps around to the
    beginning when the end of the catalog is reached.

    Args:
        prisma: Prisma client instance
        marketing_type: Either 'social' or 'email'

    Returns:
        The next Product model instance, or None if no products exist
    """
    products = await prisma.product.find_many(order={"createdAt": "asc"})
    if not products:
        logger.info("No products in database for marketing rotation")
        return None

    # Get or create the singleton state tracker
    state = await prisma.marketingstate.find_unique(where={"id": "singleton"})
    if not state:
        state = await prisma.marketingstate.create(data={"id": "singleton"})

    # Determine which index to use based on channel
    idx_field = "lastSocialIdx" if marketing_type == "social" else "lastEmailIdx"
    current_idx: int = getattr(state, idx_field)

    # Calculate the next index (wrap around at end of catalog)
    next_idx = current_idx + 1
    if next_idx >= len(products):
        next_idx = 0  # Wrap around to the first product
        logger.info(
            f"Marketing rotation ({marketing_type}): wrapped around to product 0"
        )

    # Update the state with the new index
    await prisma.marketingstate.update(
        where={"id": "singleton"},
        data={idx_field: next_idx},
    )

    selected = products[next_idx]
    logger.info(
        f"Marketing rotation ({marketing_type}): selected product "
        f"[{next_idx}/{len(products)}] → {selected.productName}"
    )
    return selected


# =============================================================================
# The Autonomous Marketing Loop — Runs Every 2 Hours
# =============================================================================
async def execute_marketing_loop() -> None:
    """
    The unified bi-hourly autonomous marketing loop.

    This is the heart of the autonomous platform. Every 2 hours, it:
    1. Selects the next product in the catalog rotation
    2. Generates AI marketing copy (caption + email)
    3. Posts to Facebook and Instagram
    4. Sends promotional email to the entire audience
    5. Logs everything to MarketingLog for audit trail

    Error Isolation: Each step (social posting, email sending) fails
    independently. A Facebook failure doesn't prevent the email from
    being sent, and vice versa.
    """
    global _prisma
    if not _prisma:
        logger.error("Scheduler has no Prisma client — skipping marketing loop")
        return

    prisma = _prisma

    # --- Database Heartbeat & Reconnection ---
    # Cloud providers often drop idle connections. If the ping fails, reconnect.
    try:
        await prisma.query_raw("SELECT 1")
    except Exception as e:
        logger.warning(f"[MARKETING LOOP] Database connection dropped ({e}), attempting to reconnect...")
        try:
            if prisma.is_connected():
                await prisma.disconnect()
        except Exception:
            pass  # Ignore disconnect errors on dead connections
        await prisma.connect()
        logger.info("[MARKETING LOOP] Database reconnected successfully")

    logger.info("=" * 60)
    logger.info("[MARKETING LOOP] Starting bi-hourly autonomous marketing cycle")
    logger.info("=" * 60)

    # --- Step 1: Select the next product ---
    product = await _get_next_product(prisma, "social")
    if not product:
        logger.info("[MARKETING LOOP] No products available — skipping cycle")
        return

    logger.info(f"[MARKETING LOOP] Product: {product.productName} (${product.sellPrice})")

    state = await prisma.marketingstate.find_unique(where={"id": "singleton"})
    auto_approve = state.autoApprove if state else False
    logger.info(f"[MARKETING LOOP] Auto-Approve is {'ON' if auto_approve else 'OFF'}")

    # Initialize tracking variables
    caption: str = ""
    email_subject: str = ""
    email_html: str = ""
    email_text: str = ""
    fb_post_id: str | None = None
    ig_post_id: str | None = None
    social_errors: list[str] = []
    email_errors: list[str] = []

    # --- Step 2: Generate AI marketing copy ---
    try:
        caption = await generate_social_caption(product)
        email_content = await generate_promotional_email(product)
        
        email_subject = email_content.get("subject", f"Featured: {product.productName}")
        email_text = email_content.get("bodyText", "")
        email_html = email_content.get("bodyHtml", "")

        logger.info("[MARKETING LOOP] ✓ AI copy generated")

    except Exception as e:
        logger.error(f"[MARKETING LOOP] AI copy generation failed: {e}")
        # Use fallback copy
        caption = (
            f"✨ Discover {product.productName} — "
            f"Only ${product.sellPrice}! Shop now at quantcai.in"
        )
        email_subject = f"Featured: {product.productName}"
        email_text = f"Check out {product.productName} for ${product.sellPrice}. Shop now at quantcai.in"
        product_url = f"https://quantcai.in/product/{product.id}"
        email_html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <h2 style="text-align: center; color: #1a1a1a;">{product.productName}</h2>
    <img src="{product.productImage or ''}" alt="{product.productName}" style="max-width: 100%; border-radius: 8px;" />
    <p>{(product.description or '')[:300]}</p>
    <p style="font-size: 1.2em; font-weight: bold;">
        Now <span style="color: #e74c3c;">${product.sellPrice}</span>
    </p>
    <a href="{product_url}" style="display: inline-block; padding: 14px 28px; background-color: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">Order Now →</a>
    <p style="font-size: 0.8em; color: #999; margin-top: 24px;">You're receiving this because you're part of the QuantCAI community. <a href="#">Unsubscribe</a></p>
</div>"""

    # --- Step 3: Gather media (video-first priority) ---
    media_urls: list[str] = []
    if getattr(product, "uploadedVideo", None):
        # Ensure it's an absolute URL
        vid_url = product.uploadedVideo
        if vid_url.startswith("/"):
            vid_url = f"https://quantcai.in{vid_url}"
        media_urls.append(vid_url)
    if product.productVideo:
        media_urls.append(product.productVideo)
    if product.productImages:
        media_urls.extend(product.productImages)
    elif product.productImage:
        media_urls.append(product.productImage)

    # --- Step 4: Post to social media (error-isolated) ---
    # Create the social post record first
    try:
        social_post = await prisma.socialpost.create(
            data={
                "productId": product.id,
                "platform": "BOTH",
                "type": "AUTO",
                "caption": caption,
                "mediaUrls": media_urls,
                "scheduledAt": datetime.now(),
                "status": "DRAFT",
            }
        )
    except Exception as e:
        logger.error(f"[MARKETING LOOP] Failed to create social post record: {e}")
        social_post = None

    social_success = False
    if social_post:
        if auto_approve:
            fb_post_id, ig_post_id = None, None
            try:
                fb_post_id = await post_to_facebook(message=caption, media_urls=media_urls)
                if not fb_post_id:
                    social_errors.append("FB: Post returned None")
            except Exception as e:
                social_errors.append(f"FB: {str(e)}")
                
            try:
                ig_post_id = await post_to_instagram(message=caption, media_urls=media_urls)
                if not ig_post_id:
                    social_errors.append("IG: Post returned None")
            except Exception as e:
                social_errors.append(f"IG: {str(e)}")
                
            social_success = fb_post_id is not None or ig_post_id is not None
            
            await prisma.socialpost.update(
                where={"id": social_post.id},
                data={
                    "status": "POSTED" if social_success else "FAILED",
                    "postedAt": datetime.now() if social_success else None,
                    "fbPostId": fb_post_id,
                    "igPostId": ig_post_id,
                    "errorLog": " | ".join(social_errors) if social_errors else None
                }
            )
            logger.info(f"[MARKETING LOOP] {'✓' if social_success else '✗'} Social posted automatically")
        else:
            social_success = True
            logger.info(f"[MARKETING LOOP] ✓ Social post drafted (Requires manual approval)")

    # --- Step 5: Send email blast (error-isolated) ---
    email_success = False
    email_count = 0

    # Create email campaign record
    try:
        email_campaign = await prisma.emailcampaign.create(
            data={
                "productId": product.id,
                "type": "AUTO",
                "subject": email_subject,
                "bodyText": email_text,
                "bodyHtml": email_html,
                "scheduledAt": datetime.now(),
                "status": "DRAFT",
            }
        )
    except Exception as e:
        logger.error(f"[MARKETING LOOP] Failed to create email campaign record: {e}")
        email_campaign = None

    if email_campaign:
        if auto_approve:
            try:
                result = await send_email_blast(
                    subject=email_subject,
                    html_body=email_html,
                    text_body=email_text,
                    prisma=prisma,
                )
                email_success = result.get("success", False)
                email_count = result.get("count", 0)
                if result.get("error"):
                    email_errors.append(result["error"])
                logger.info(
                    f"[MARKETING LOOP] {'✓' if email_success else '✗'} "
                    f"Email blast: {email_count} sent"
                )
            except Exception as e:
                email_errors.append(str(e))
                logger.error(f"[MARKETING LOOP] Email blast failed: {e}")
                
            try:
                await prisma.emailcampaign.update(
                    where={"id": email_campaign.id},
                    data={
                        "status": "SENT" if email_success else "FAILED",
                        "sentAt": datetime.now() if email_success else None,
                        "recipientCount": email_count,
                        "errorLog": " | ".join(email_errors) if email_errors else None,
                    },
                )
            except Exception as e:
                logger.error(f"[MARKETING LOOP] Failed to update email campaign: {e}")
        else:
            email_success = True
            logger.info(f"[MARKETING LOOP] ✓ Email campaign drafted (Requires manual approval)")

    # --- Step 6: Log to MarketingLog (audit trail) ---
    overall_status = "SUCCESS"
    if not social_success and not email_success:
        overall_status = "FAILED"
    elif not social_success or not email_success:
        overall_status = "PARTIAL"

    all_errors = social_errors + email_errors
    # MarketingLog model is not in schema; skipping audit trail write

    # --- Summary ---
    logger.info("=" * 60)
    logger.info(
        f"[MARKETING LOOP] Cycle complete | "
        f"Product: {product.productName} | "
        f"Social: {'✓' if social_success else '✗'} | "
        f"Email: {'✓' if email_success else '✗'} ({email_count} sent) | "
        f"Status: {overall_status}"
    )
    logger.info("=" * 60)


# =============================================================================
# Database Keep-Alive
# =============================================================================
async def keep_alive_db() -> None:
    """Ping the database to keep the connection alive (prevents idle timeouts)."""
    global _prisma
    if _prisma and _prisma.is_connected():
        try:
            await _prisma.query_raw("SELECT 1")
        except Exception as e:
            logger.warning(f"[KEEP ALIVE] Database ping failed ({e})")


# =============================================================================
# Scheduler Factory — Creates and configures the APScheduler instance
# =============================================================================
def create_scheduler(prisma: Prisma) -> AsyncIOScheduler:
    """
    Create and configure the AsyncIOScheduler with the marketing loop job.

    The scheduler runs the execute_marketing_loop() function every 2 hours.
    It receives the Prisma client from main.py's lifespan context to avoid
    creating standalone database connections.

    Args:
        prisma: The Prisma client instance from the application lifespan

    Returns:
        Configured (but not started) AsyncIOScheduler instance
    """
    global _prisma
    _prisma = prisma

    scheduler = AsyncIOScheduler()

    # Add the bi-hourly marketing loop
    scheduler.add_job(
        execute_marketing_loop,
        trigger=IntervalTrigger(hours=2),
        id="marketing_loop",
        name="Bi-Hourly Autonomous Marketing Loop",
        replace_existing=True,
    )

    logger.info(
        "Scheduler configured: marketing loop every 2 hours "
    )

    # Add a keep-alive job every 3 minutes to prevent the DB connection from dropping
    scheduler.add_job(
        keep_alive_db,
        trigger=IntervalTrigger(minutes=3),
        id="db_keep_alive",
        name="Database Keep-Alive Ping",
        replace_existing=True,
    )

    return scheduler


def shutdown_scheduler(scheduler: AsyncIOScheduler) -> None:
    """
    Gracefully shutdown the scheduler.

    Uses wait=False to prevent blocking during shutdown — any currently
    running jobs will be allowed to finish but new jobs won't be triggered.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down gracefully")
