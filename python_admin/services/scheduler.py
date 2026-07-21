"""
=============================================================================
QuantCAI — Marketing Automation Scheduler (6-Hour Autonomous Loop)
=============================================================================
Implements the autonomous marketing loop that runs every 6 hours:

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

from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from prisma import Prisma

from services.ai_service import (
    generate_campaign_variation,
    generate_campaign_email,
    generate_arxiv_content,
    _classify_paper_category,
    _build_arxiv_cta_link,
)
from services.email_service import send_email_blast
from services.social_service import post_to_facebook, post_to_instagram
from services.twitter_service import twitter_service
from services.linkedin_service import linkedin_service
from services.arxiv_newsroom import (
    ArxivRegistry,
    fetch_and_filter_new_papers,
)

# =============================================================================
# Module-level Prisma reference (set during scheduler creation)
# =============================================================================
# This is set by create_scheduler() and used by the scheduled tasks.
# It's the SAME instance created in main.py's lifespan context.
_prisma: Prisma | None = None


# =============================================================================
# Campaign Rotation — Sequential Round-Robin
# =============================================================================
async def _get_next_campaign(
    prisma: Prisma, marketing_type: str
) -> Any | None:
    """
    Get the next active campaign in the sequential rotation.
    """
    campaigns = await prisma.socialcampaign.find_many(where={"isActive": True}, order={"createdAt": "asc"})
    if not campaigns:
        logger.info("No active campaigns in database for marketing rotation")
        return None

    state = await prisma.marketingstate.find_unique(where={"id": "singleton"})
    if not state:
        state = await prisma.marketingstate.create(data={"id": "singleton"})

    idx_field = "lastSocialIdx" if marketing_type == "social" else "lastEmailIdx"
    current_idx: int = getattr(state, idx_field)

    next_idx = current_idx + 1
    if next_idx >= len(campaigns):
        next_idx = 0
        logger.info(f"Marketing rotation ({marketing_type}): wrapped around to campaign 0")

    await prisma.marketingstate.update(
        where={"id": "singleton"},
        data={idx_field: next_idx},
    )

    selected = campaigns[next_idx]
    logger.info(
        f"Marketing rotation ({marketing_type}): selected campaign "
        f"[{next_idx}/{len(campaigns)}] → {selected.id}"
    )
    return selected

# =============================================================================
# The Autonomous Marketing Loop — Runs Every 6 Hours
# =============================================================================
async def execute_marketing_loop() -> None:
    """
    The unified 6-hour autonomous marketing loop.

    This is the heart of the autonomous platform. Every 6 hours, it:
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
    logger.info("[MARKETING LOOP] Starting 6-hour autonomous marketing cycle")
    logger.info("=" * 60)

    campaign = await _get_next_campaign(prisma, "social")
    if not campaign:
        logger.info("[MARKETING LOOP] No active campaigns available — skipping cycle")
        return

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
    tw_post_id: str | None = None
    li_post_id: str | None = None
    social_errors: list[str] = []
    email_errors: list[str] = []
    media_urls: list[str] = []
    
    social_success = False
    email_success = False
    email_count = 0

    try:
        caption = await generate_campaign_variation(campaign.baseCaption)
        email_content = await generate_campaign_email(campaign)
        email_subject = email_content.get("subject", "QuantCAI Update")
        email_text = email_content.get("bodyText", "")
        email_html = email_content.get("bodyHtml", "")
        logger.info("[MARKETING LOOP] ✓ AI campaign content generated")
    except Exception as e:
        logger.error(f"[MARKETING LOOP] AI generation failed: {e}")
        caption = campaign.baseCaption
        email_subject = "QuantCAI Update"
        email_text = campaign.baseCaption
        email_html = f"<p>{campaign.baseCaption}</p>"

    # Ensure media URL is absolute
    vid_url = campaign.mediaUrl
    if vid_url.startswith("/"):
        vid_url = f"https://quantcai.in{vid_url}"
    media_urls = [vid_url]

    # --- Step 4: Post to social media (error-isolated) ---
    # Create the social post record first
    try:
        social_post = await prisma.socialpost.create(
            data={
                "campaignId": campaign.id,
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
            fb_post_id, ig_post_id, tw_post_id, li_post_id = None, None, None, None
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
                
            if twitter_service.is_available:
                try:
                    # For Twitter, generate a thread if caption is long
                    if len(caption) > 280:
                        tweets = await twitter_service.generate_thread_from_caption(caption, "#QuantCAI #PQC")
                        thread_ids = await twitter_service.post_thread(tweets)
                        if thread_ids:
                            tw_post_id = thread_ids[0]
                        else:
                            social_errors.append("TW: Thread posting failed")
                    else:
                        tw_post_id = await twitter_service.post_tweet(caption)
                        if not tw_post_id:
                            social_errors.append("TW: Post returned None")
                except Exception as e:
                    social_errors.append(f"TW: {str(e)}")

            if linkedin_service.is_available:
                try:
                    li_copy = await linkedin_service.format_b2b_copy(caption)
                    li_post_id = await linkedin_service.post_article(
                        text=li_copy,
                        article_url=media_urls[0] if media_urls else "https://quantcai.in",
                        article_title="QuantCAI Enterprise Infrastructure",
                    )
                    if not li_post_id:
                        social_errors.append("LI: Post returned None")
                except Exception as e:
                    social_errors.append(f"LI: {str(e)}")
                
            social_success = any([fb_post_id, ig_post_id, tw_post_id, li_post_id])
            
            await prisma.socialpost.update(
                where={"id": social_post.id},
                data={
                    "status": "POSTED" if social_success else "FAILED",
                    "postedAt": datetime.now() if social_success else None,
                    "fbPostId": fb_post_id,
                    "igPostId": ig_post_id,
                    "twitterPostId": tw_post_id,
                    "linkedinPostId": li_post_id,
                    "errorLog": " | ".join(social_errors) if social_errors else None
                }
            )
            logger.info(f"[MARKETING LOOP] {'✓' if social_success else '✗'} Social posted automatically")
        else:
            social_success = True
            logger.info(f"[MARKETING LOOP] ✓ Social post drafted (Requires manual approval)")

    # --- Step 5: Send email blast (error-isolated) ---
    email_campaign = None
    try:
        email_campaign = await prisma.emailcampaign.create(
            data={
                "campaignId": campaign.id,
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
    try:
        await prisma.marketinglog.create(
            data={
                "campaignId": campaign.id,
                "status": overall_status,
                "socialSuccess": social_success,
                "emailSuccess": email_success,
                "emailCount": email_count,
                "errorLog": " | ".join(all_errors) if all_errors else None
            }
        )
        logger.info("[MARKETING LOOP] ✓ Audit trail logged successfully")
    except Exception as e:
        logger.error(f"[MARKETING LOOP] Failed to write audit trail: {e}")

    # --- Summary ---
    logger.info("=" * 60)
    logger.info(
        f"[MARKETING LOOP] Cycle complete | "
        f"Campaign: {campaign.id} | "
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
# Autonomous arXiv Newsroom Loop — Runs Every 12 Hours
# =============================================================================
async def execute_arxiv_newsroom_loop() -> None:
    """
    The autonomous arXiv research-to-social pipeline.

    Every 12 hours, this loop:
    1. Fetches the latest papers from quant-ph and cs.CR on arXiv
    2. Filters out already-processed papers via SQLite registry
    3. Generates AI-powered X threads and LinkedIn posts for each paper
    4. Posts to X (Twitter) and LinkedIn
    5. Marks papers as processed in the registry

    This loop runs INDEPENDENTLY from the 6-hour marketing campaign loop.
    Error handling is per-paper — one failure doesn't block the rest.
    """
    logger.info("=" * 60)
    logger.info("[ARXIV NEWSROOM] Starting 12-hour arXiv research scan")
    logger.info("=" * 60)

    registry = ArxivRegistry()
    papers_posted = 0
    papers_failed = 0

    try:
        new_papers = await fetch_and_filter_new_papers(
            registry=registry,
            max_results=15,  # 15 per category = 30 total max, typically ~5-10 new
        )
    except Exception as e:
        logger.error(f"[ARXIV NEWSROOM] Failed to fetch papers: {e}")
        return

    if not new_papers:
        logger.info("[ARXIV NEWSROOM] No new papers found — skipping cycle")
        return

    # Process up to 5 papers per cycle to avoid API rate limits and content fatigue
    papers_to_process = new_papers[:5]
    logger.info(
        f"[ARXIV NEWSROOM] Processing {len(papers_to_process)} papers "
        f"(of {len(new_papers)} new)"
    )

    for paper in papers_to_process:
        x_posted = False
        li_posted = False

        try:
            # Generate AI content
            content = await generate_arxiv_content(
                title=paper.title,
                abstract=paper.abstract,
                arxiv_id=paper.arxiv_id,
            )

            x_thread = content["x_thread"]
            li_post = content["linkedin_post"]

            logger.info(
                f"[ARXIV NEWSROOM] ✓ AI content generated for {paper.arxiv_id} "
                f"(category: {content['category']})"
            )

            # --- Post to X (Twitter) as a thread ---
            if twitter_service.is_available:
                try:
                    tweets = [
                        x_thread["post_1"],
                        x_thread["post_2"],
                        x_thread["post_3"],
                    ]
                    # Append hashtags to the last tweet
                    hashtag_str = " ".join(x_thread.get("hashtags", []))
                    if hashtag_str and len(tweets[-1]) + len(hashtag_str) + 2 <= 280:
                        tweets[-1] = f"{tweets[-1]}\n\n{hashtag_str}"

                    thread_ids = await twitter_service.post_thread(tweets)
                    if thread_ids:
                        x_posted = True
                        logger.info(
                            f"[ARXIV NEWSROOM] ✓ X thread posted for {paper.arxiv_id}: "
                            f"{len(thread_ids)} tweets"
                        )
                except Exception as e:
                    logger.error(f"[ARXIV NEWSROOM] X posting failed for {paper.arxiv_id}: {e}")

            # --- Post to LinkedIn ---
            if linkedin_service.is_available:
                try:
                    li_body = li_post["body"]
                    hashtag_str = " ".join(li_post.get("hashtags", []))
                    if hashtag_str:
                        li_body = f"{li_body}\n\n{hashtag_str}"

                    li_post_id = await linkedin_service.post_article(
                        text=li_body,
                        article_url=paper.abs_url or f"https://arxiv.org/abs/{paper.arxiv_id}",
                        article_title=paper.title,
                        article_description=paper.abstract[:200],
                    )
                    if li_post_id:
                        li_posted = True
                        logger.info(
                            f"[ARXIV NEWSROOM] ✓ LinkedIn post published for {paper.arxiv_id}"
                        )
                except Exception as e:
                    logger.error(f"[ARXIV NEWSROOM] LinkedIn posting failed for {paper.arxiv_id}: {e}")

            # Mark as processed regardless of posting success
            # (prevents re-processing on next cycle)
            registry.mark_processed(
                arxiv_id=paper.arxiv_id,
                title=paper.title,
                category=content["category"],
                x_posted=x_posted,
                linkedin_posted=li_posted,
            )

            if x_posted or li_posted:
                papers_posted += 1
            else:
                papers_failed += 1

        except Exception as e:
            logger.error(f"[ARXIV NEWSROOM] Failed to process {paper.arxiv_id}: {e}")
            # Still mark as processed to avoid infinite retries on bad data
            registry.mark_processed(
                arxiv_id=paper.arxiv_id,
                title=paper.title,
            )
            papers_failed += 1

    # --- Summary ---
    stats = registry.get_stats()
    logger.info("=" * 60)
    logger.info(
        f"[ARXIV NEWSROOM] Cycle complete | "
        f"Posted: {papers_posted} | Failed: {papers_failed} | "
        f"Total processed (all time): {stats['total_processed']}"
    )
    logger.info("=" * 60)


# =============================================================================
# Scheduler Factory — Creates and configures the APScheduler instance
# =============================================================================
def create_scheduler(prisma: Prisma) -> AsyncIOScheduler:
    """
    Create and configure the AsyncIOScheduler with all automation jobs:
    1. Marketing campaign loop (every 6 hours)
    2. arXiv newsroom loop (every 12 hours)
    3. Database keep-alive (every 3 minutes)

    Args:
        prisma: The Prisma client instance from the application lifespan

    Returns:
        Configured (but not started) AsyncIOScheduler instance
    """
    global _prisma
    _prisma = prisma

    scheduler = AsyncIOScheduler(timezone=timezone.utc)

    # --- 6-hour marketing campaign loop ---
    scheduler.add_job(
        execute_marketing_loop,
        trigger=IntervalTrigger(hours=6),
        id="marketing_loop",
        name="6-Hour Autonomous Marketing Loop",
        replace_existing=True,
    )

    # --- 12-hour arXiv newsroom loop ---
    scheduler.add_job(
        execute_arxiv_newsroom_loop,
        trigger=IntervalTrigger(hours=12),
        id="arxiv_newsroom_loop",
        name="12-Hour Autonomous arXiv Newsroom",
        replace_existing=True,
    )

    logger.info(
        "Scheduler configured: marketing loop every 6 hours, "
        "arXiv newsroom every 12 hours"
    )

    # --- Keep-alive ping every 3 minutes ---
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
