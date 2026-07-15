"""
=============================================================================
QuantCAI — LinkedIn API Service
=============================================================================
Automated LinkedIn Company Page publishing via the LinkedIn REST API.
Supports text posts and article sharing with rich media previews.

Required environment variables:
  - LINKEDIN_ACCESS_TOKEN    (OAuth 2.0 token with w_organization_social scope)
  - LINKEDIN_ORGANIZATION_ID (LinkedIn Company Page numeric ID)

LinkedIn Developer Portal must have "Share on LinkedIn" product approved
and the authenticating user must be an admin of the Company Page.
=============================================================================
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger("quantcai.linkedin")

LINKEDIN_API_BASE = "https://api.linkedin.com"
LINKEDIN_API_VERSION = "202406"  # LinkedIn versioned API: YYYYMM


class LinkedInService:
    """
    LinkedIn REST API client for automated Company Page publishing.
    Uses the Versioned API with w_organization_social scope.
    """

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.org_id = os.getenv("LINKEDIN_ORGANIZATION_ID", "")
        self._available = False

        if self.access_token and self.org_id:
            self._available = True
            logger.info("LinkedIn API service initialized.")
        else:
            logger.warning("LinkedIn API credentials not configured — skipping LinkedIn integration.")

    @property
    def is_available(self) -> bool:
        return self._available

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def post_text(self, text: str) -> Optional[str]:
        """
        Publish a text-only post to the LinkedIn Company Page.
        
        Args:
            text: Post content (max ~3000 chars recommended).
        
        Returns:
            LinkedIn post URN on success, None on failure.
        """
        if not self._available:
            return None

        payload = {
            "author": f"urn:li:organization:{self.org_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{LINKEDIN_API_BASE}/rest/posts",
                    headers=self._headers(),
                    json=payload,
                )

                if resp.status_code in (200, 201):
                    # LinkedIn returns the post URN in the x-restli-id header
                    post_id = resp.headers.get("x-restli-id", "")
                    logger.info(f"LinkedIn post published: {post_id}")
                    return post_id
                else:
                    logger.error(f"LinkedIn post failed [{resp.status_code}]: {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"LinkedIn API error: {e}")
            return None

    async def post_article(
        self,
        text: str,
        article_url: str,
        article_title: str,
        article_description: str = "",
    ) -> Optional[str]:
        """
        Share an article link on the LinkedIn Company Page with rich preview.
        
        Note: LinkedIn does not reliably scrape OG metadata automatically.
        We must explicitly provide title, description, and the source URL.
        
        Args:
            text: Post commentary text.
            article_url: URL of the article to share.
            article_title: Title for the article preview card.
            article_description: Description for the preview card.
        
        Returns:
            LinkedIn post URN on success, None on failure.
        """
        if not self._available:
            return None

        payload = {
            "author": f"urn:li:organization:{self.org_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "article": {
                    "source": article_url,
                    "title": article_title,
                    "description": article_description or text[:200],
                },
            },
            "lifecycleState": "PUBLISHED",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{LINKEDIN_API_BASE}/rest/posts",
                    headers=self._headers(),
                    json=payload,
                )

                if resp.status_code in (200, 201):
                    post_id = resp.headers.get("x-restli-id", "")
                    logger.info(f"LinkedIn article shared: {post_id}")
                    return post_id
                else:
                    logger.error(f"LinkedIn article share failed [{resp.status_code}]: {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"LinkedIn API error: {e}")
            return None

    async def format_b2b_copy(self, caption: str, cta_url: str = "https://quantcai.in") -> str:
        """
        Format a marketing caption into LinkedIn-optimized B2B copy.
        LinkedIn posts perform best with:
        - Opening hook (first 2 lines visible before "see more")
        - Bullet points for scanability
        - Clear CTA at the bottom
        - Hashtags at the very end
        """
        lines = caption.strip().split("\n")
        hook = lines[0] if lines else caption[:150]

        formatted = f"""{hook}

{caption}

🔗 Learn more: {cta_url}

#PostQuantumCryptography #QuantumComputing #Cybersecurity #NIST #PQC #QuantumSafe #TechSecurity"""

        return formatted


# ─── Singleton ───────────────────────────────────────────────────────
linkedin_service = LinkedInService()
