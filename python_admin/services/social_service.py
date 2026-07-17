"""
=============================================================================
Lumively — Meta Graph API Client (Facebook + Instagram Publishing)
=============================================================================
Implements container-based publishing for Instagram and direct publishing
for Facebook, with full video/image/carousel handling.

Publishing Logic (Priority Order):
  1. If a video link exists → Post as REELS (Instagram) / Video (Facebook)
  2. If multiple images → Post as Carousel
  3. If single image → Post as single image
  4. Text-only fallback for Facebook (Instagram requires media)

Instagram Container Flow:
  1. Create media container via POST {ig-user-id}/media
  2. Asynchronous polling via asyncio.sleep to check container readiness
  3. Publish via POST {ig-user-id}/media_publish

All HTTP calls are fully async via httpx with exponential backoff.
Error handling catches "Unsupported post request" without crashing.
=============================================================================
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings

# =============================================================================
# Constants
# =============================================================================
GRAPH_API_VERSION = "v19.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Timeout for Meta API calls (video uploads can be slow)
META_TIMEOUT = httpx.Timeout(60.0, connect=15.0)

# Instagram container polling settings
CONTAINER_POLL_INTERVAL = 5  # seconds between status checks
CONTAINER_POLL_MAX_ATTEMPTS = 24  # max 2 minutes of polling (24 * 5s)


# =============================================================================
# Helper — Detect video URLs
# =============================================================================
def _is_video(url: str) -> bool:
    """Check if a URL points to a video file based on extension or query param."""
    if not url:
        return False
    url_lower = url.lower()
    if "type=video" in url_lower:
        return True
    
    # Check if any common video extension is present in the URL (handles query params like ?type=.mp4)
    if any(ext in url_lower for ext in [".mp4", ".mov", ".webm", ".avi"]):
        return True
        
    return False


# =============================================================================
# HTTP Helper — Retry-wrapped async POST to Graph API
# =============================================================================
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Meta API retry attempt {retry_state.attempt_number}"
    ),
)
async def _graph_post(url: str, data: dict[str, Any]) -> dict:
    """POST to the Meta Graph API with exponential backoff retry."""
    async with httpx.AsyncClient(timeout=META_TIMEOUT) as client:
        response = await client.post(url, data=data)
        if response.is_error:
            logger.error(f"Meta Graph API Error: {response.status_code} - {response.text}")
            try:
                error_code = response.json().get("error", {}).get("code")
                if error_code == 190:
                    raise ValueError(f"Meta Graph API OAuth Error: {response.text}")
            except ValueError:
                raise
            except Exception:
                pass
        response.raise_for_status()
        return response.json()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
async def _graph_get(url: str, params: dict[str, str]) -> dict:
    """GET from the Meta Graph API with exponential backoff retry."""
    async with httpx.AsyncClient(timeout=META_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _get_fb_credentials() -> tuple[str | None, str | None]:
    """Get Facebook Page credentials from settings."""
    return settings.fb_page_access_token, settings.fb_page_id


def _get_ig_credentials() -> tuple[str | None, str | None]:
    """Get Instagram Business Account credentials from settings."""
    return settings.fb_page_access_token, settings.ig_business_account_id


# =============================================================================
# Facebook Publishing
# =============================================================================
async def post_to_facebook(
    message: str, media_urls: list[str] | None = None
) -> str | None:
    """
    Post content to the Facebook Page.

    Enterprise Logic:
    - Videos: Posted individually to /{page-id}/videos (Native Video/Reels).
    - Images: Grouped into a single multi-photo feed post (or single photo post).
    - Returns a comma-separated list of all successful post IDs.

    Args:
        message: The post caption/message text
        media_urls: Optional list of media URLs (images and/or videos)

    Returns:
        The Facebook post ID string (comma-separated if multiple), or None on failure
    """
    access_token, page_id = _get_fb_credentials()
    if not access_token or not page_id:
        logger.warning("Facebook credentials missing — skipping post")
        return None

    if not media_urls:
        media_urls = []

    # Ensure absolute URLs for Facebook API
    media_urls = [f"https://quantcai.in{url}" if url.startswith("/") else url for url in media_urls]

    video_urls = [url for url in media_urls if _is_video(url)]
    image_urls = [url for url in media_urls if not _is_video(url)]

    post_ids = []

    # --- 1. Post Each Video Separately ---
    for vid_url in video_urls:
        url = f"{GRAPH_BASE_URL}/{page_id}/videos"
        payload = {
            "access_token": access_token,
            "description": message,
            "file_url": vid_url,
        }
        try:
            result = await _graph_post(url, payload)
            post_id = result.get("id")
            if post_id:
                logger.info(f"✓ Facebook video posted: {post_id}")
                post_ids.append(post_id)
        except Exception as e:
            logger.error(f"Facebook video post failed: {e}")

    # --- 2. Post Images ---
    if len(image_urls) > 1:
        # Multi-image carousel-style post (upload unpublished, then combine)
        attached_media: list[dict[str, str]] = []
        for img_url in image_urls[:10]:
            photo_payload = {
                "access_token": access_token,
                "url": img_url,
                "published": "false",
            }
            try:
                res = await _graph_post(f"{GRAPH_BASE_URL}/{page_id}/photos", photo_payload)
                media_id = res.get("id")
                if media_id:
                    attached_media.append({"media_fbid": media_id})
            except Exception as e:
                logger.warning(f"Failed to upload unpublished FB photo: {e}")

        if attached_media:
            import json as json_lib
            feed_payload = {
                "access_token": access_token,
                "message": message,
                "attached_media": json_lib.dumps(attached_media),
            }
            try:
                result = await _graph_post(f"{GRAPH_BASE_URL}/{page_id}/feed", feed_payload)
                post_id = result.get("id")
                if post_id:
                    logger.info(f"✓ Facebook multi-photo post created: {post_id}")
                    post_ids.append(post_id)
            except Exception as e:
                logger.error(f"Facebook multi-photo post failed: {e}")

    elif len(image_urls) == 1:
        # Single image
        url = f"{GRAPH_BASE_URL}/{page_id}/photos"
        payload = {
            "access_token": access_token,
            "message": message,
            "url": image_urls[0],
        }
        try:
            result = await _graph_post(url, payload)
            post_id = result.get("post_id") or result.get("id")
            if post_id:
                logger.info(f"✓ Facebook single image posted: {post_id}")
                post_ids.append(post_id)
        except Exception as e:
            logger.error(f"Facebook image post failed: {e}")

    # --- 3. Text only (if no media was provided) ---
    if not video_urls and not image_urls:
        url = f"{GRAPH_BASE_URL}/{page_id}/feed"
        payload = {
            "access_token": access_token,
            "message": message,
        }
        try:
            result = await _graph_post(url, payload)
            post_id = result.get("id")
            if post_id:
                logger.info(f"✓ Facebook text posted: {post_id}")
                post_ids.append(post_id)
        except Exception as e:
            logger.error(f"Facebook text post failed: {e}")

    if not post_ids:
        return None
    return ",".join(post_ids)


# =============================================================================
# Instagram Container Polling
# =============================================================================
async def _poll_container_status(
    container_id: str, access_token: str
) -> bool:
    """
    Asynchronously poll an Instagram media container until it's ready.

    Instagram containers go through processing stages:
    - IN_PROGRESS: Still processing (especially videos)
    - FINISHED: Ready to publish
    - ERROR: Processing failed

    Uses asyncio.sleep for non-blocking waits between polls.

    Args:
        container_id: The Instagram container/creation ID
        access_token: The Page access token

    Returns:
        True if the container is ready (FINISHED), False on error/timeout
    """
    url = f"{GRAPH_BASE_URL}/{container_id}"
    params = {
        "fields": "status_code",
        "access_token": access_token,
    }

    for attempt in range(CONTAINER_POLL_MAX_ATTEMPTS):
        try:
            result = await _graph_get(url, params)
            status = result.get("status_code", "IN_PROGRESS")

            if status == "FINISHED":
                logger.info(
                    f"✓ IG container {container_id} ready "
                    f"(polled {attempt + 1} times)"
                )
                return True
            elif status == "ERROR":
                logger.error(
                    f"IG container {container_id} failed processing"
                )
                return False
            else:
                # Still processing — wait and try again
                logger.debug(
                    f"IG container {container_id} status: {status} "
                    f"(attempt {attempt + 1}/{CONTAINER_POLL_MAX_ATTEMPTS})"
                )
                await asyncio.sleep(CONTAINER_POLL_INTERVAL)

        except Exception as e:
            logger.warning(f"IG container poll error: {e}")
            await asyncio.sleep(CONTAINER_POLL_INTERVAL)

    logger.error(
        f"IG container {container_id} timed out after "
        f"{CONTAINER_POLL_MAX_ATTEMPTS * CONTAINER_POLL_INTERVAL}s"
    )
    return False


# =============================================================================
# Instagram Publishing
# =============================================================================
async def post_to_instagram(
    message: str, media_urls: list[str] | None = None
) -> str | None:
    """
    Post content to Instagram using the container-based publishing flow.

    Flow:
    1. Create a media container (image, video/REELS, or carousel)
    2. Poll the container status until FINISHED
    3. Publish the container

    Priority:
    - Video links → REELS
    - Multiple images → Carousel
    - Single image → Standard image post

    Args:
        message: The post caption
        media_urls: List of media URLs (required — IG needs at least one)

    Returns:
        The Instagram post ID string, or None on failure
    """
    access_token, ig_user_id = _get_ig_credentials()
    if not access_token or not ig_user_id:
        logger.warning("Instagram credentials missing — skipping post")
        return None

    if not media_urls:
        logger.warning("Instagram requires at least one media URL")
        return None

    # Ensure absolute URLs for Instagram API
    media_urls = [f"https://quantcai.in{url}" if url.startswith("/") else url for url in media_urls]

    # Separate videos and images
    video_urls = [url for url in media_urls if _is_video(url)]
    image_urls = [url for url in media_urls if not _is_video(url)]

    post_ids = []

    # --- Post each video as a separate REEL ---
    for vid_url in video_urls:
        vid_id = await _ig_post_video(ig_user_id, access_token, message, vid_url)
        if vid_id:
            post_ids.append(vid_id)

    # --- Post images as Carousel or Single Image ---
    if len(image_urls) > 1:
        img_id = await _ig_post_carousel(ig_user_id, access_token, message, image_urls)
        if img_id:
            post_ids.append(img_id)
    elif len(image_urls) == 1:
        img_id = await _ig_post_single_image(ig_user_id, access_token, message, image_urls[0])
        if img_id:
            post_ids.append(img_id)

    if not post_ids:
        logger.warning("No successful Instagram posts created")
        return None

    return ",".join(post_ids)


async def _ig_post_video(
    ig_user_id: str, access_token: str, caption: str, video_url: str
) -> str | None:
    """Post a video as an Instagram Reel."""
    container_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media"
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }
    try:
        res = await _graph_post(container_url, container_payload)
        container_id = res.get("id")
        if not container_id:
            logger.error("Failed to create IG video container — no ID returned")
            return None

        # Poll until the video is processed and ready
        is_ready = await _poll_container_status(container_id, access_token)
        if not is_ready:
            logger.error("IG video container not ready after polling")
            return None

        # Publish
        publish_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }
        pub_res = await _graph_post(publish_url, publish_payload)
        post_id = pub_res.get("id")
        logger.info(f"✓ Instagram Reel posted: {post_id}")
        return post_id

    except Exception as e:
        # Catch "Unsupported post request" and similar errors gracefully
        _handle_ig_error("video/REELS", e)
        return None


async def _ig_post_single_image(
    ig_user_id: str, access_token: str, caption: str, image_url: str
) -> str | None:
    """Post a single image to Instagram."""
    container_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media"
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }
    try:
        res = await _graph_post(container_url, container_payload)
        container_id = res.get("id")
        if not container_id:
            return None

        # Images are usually ready immediately, but poll to be safe
        is_ready = await _poll_container_status(container_id, access_token)
        if not is_ready:
            return None

        publish_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }
        pub_res = await _graph_post(publish_url, publish_payload)
        post_id = pub_res.get("id")
        logger.info(f"✓ Instagram image posted: {post_id}")
        return post_id

    except Exception as e:
        _handle_ig_error("image", e)
        return None


async def _ig_post_carousel(
    ig_user_id: str,
    access_token: str,
    caption: str,
    image_urls: list[str],
) -> str | None:
    """Post a multi-image carousel to Instagram."""
    children_ids: list[str] = []

    # Step 1: Create individual carousel item containers
    for img_url in image_urls[:10]:  # Max 10 items per carousel
        item_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media"
        item_payload = {
            "image_url": img_url,
            "is_carousel_item": "true",
            "access_token": access_token,
        }
        try:
            res = await _graph_post(item_url, item_payload)
            item_id = res.get("id")
            if item_id:
                children_ids.append(item_id)
        except Exception as e:
            logger.warning(f"Failed to create IG carousel item: {e}")

    if not children_ids:
        logger.error("No carousel items created for Instagram")
        return None

    # Step 2: Create the carousel container
    container_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media"
    container_payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": access_token,
    }
    try:
        res = await _graph_post(container_url, container_payload)
        container_id = res.get("id")
        if not container_id:
            return None

        # Step 3: Poll until ready
        is_ready = await _poll_container_status(container_id, access_token)
        if not is_ready:
            return None

        # Step 4: Publish
        publish_url = f"{GRAPH_BASE_URL}/{ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token,
        }
        pub_res = await _graph_post(publish_url, publish_payload)
        post_id = pub_res.get("id")
        logger.info(f"✓ Instagram carousel posted: {post_id} ({len(children_ids)} items)")
        return post_id

    except Exception as e:
        _handle_ig_error("carousel", e)
        return None


def _handle_ig_error(post_type: str, error: Exception) -> None:
    """
    Handle Instagram-specific errors gracefully.
    Catches "Unsupported post request" and similar Meta API errors
    without crashing the main thread.
    """
    error_msg = str(error)
    if "Unsupported post request" in error_msg:
        logger.warning(
            f"Instagram '{post_type}' post rejected: Unsupported post request. "
            f"This usually means the media format or account type doesn't support "
            f"this post type. Skipping gracefully."
        )
    else:
        logger.error(f"Instagram '{post_type}' post failed: {error_msg}")


# =============================================================================
# Post Update Functions (for editing existing posts)
# =============================================================================
async def update_facebook_post(post_id: str, new_message: str) -> bool:
    """Update the text/message of an existing Facebook post."""
    access_token, _ = _get_fb_credentials()
    if not access_token:
        logger.warning("Facebook credentials missing — cannot update post")
        return False

    url = f"{GRAPH_BASE_URL}/{post_id}"
    payload = {
        "access_token": access_token,
        "message": new_message,
    }
    try:
        await _graph_post(url, payload)
        logger.info(f"✓ Facebook post updated: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update Facebook post {post_id}: {e}")
        return False


async def update_instagram_post(media_id: str, new_caption: str) -> bool:
    """Update the caption of an existing Instagram post."""
    access_token, _ = _get_ig_credentials()
    if not access_token:
        logger.warning("Instagram credentials missing — cannot update post")
        return False

    url = f"{GRAPH_BASE_URL}/{media_id}"
    payload = {
        "access_token": access_token,
        "caption": new_caption,
    }
    try:
        await _graph_post(url, payload)
        logger.info(f"✓ Instagram post updated: {media_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update Instagram post {media_id}: {e}")
        return False
