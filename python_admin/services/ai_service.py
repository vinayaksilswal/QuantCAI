"""
=============================================================================
QuantCAI — OpenRouter LLM Client (AI Copy & Marketing Asset Generation)
=============================================================================
Integrates with OpenRouter's API at https://openrouter.ai/api/v1/chat/completions
using the tencent/hy3:free model for marketing copy generation.

Key Functions:
  - generate_campaign_variation(): Unique variations for social media
  - generate_campaign_email(): Full email content (subject, text, HTML)

All HTTP calls are fully async via httpx with tenacity exponential backoff.
=============================================================================
"""

from __future__ import annotations

import json
import os
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

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
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# tencent/hy3:free — Used for marketing copy generation (free tier)
MARKETING_MODEL = "tencent/hy3:free"

# Shared timeout for LLM API calls (LLMs can be slow)
LLM_TIMEOUT = httpx.Timeout(60.0, connect=15.0)


# =============================================================================
# Core LLM Call — Async with Retry
# =============================================================================
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=lambda retry_state: logger.warning(
        f"OpenRouter retry attempt {retry_state.attempt_number}"
    ),
)
async def _call_openrouter(
    prompt: str,
    *,
    model: str = MARKETING_MODEL,
    json_response: bool = False,
    system_prompt: str | None = None,
) -> str:
    """
    Core async function to call OpenRouter's chat completions API.

    Args:
        prompt: The user message/prompt to send
        model: Which model to use (defaults to marketing model)
        json_response: If True, requests JSON output format
        system_prompt: Optional system message to prepend

    Returns:
        The assistant's response content as a string, or empty string on failure
    """
    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY not configured — LLM calls disabled")
        return ""

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://quantcai.in",
        "X-Title": "QuantCAI Marketing AI",
    }

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if json_response:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        return content


def _parse_json_response(text: str) -> dict | None:
    """
    Helper to parse JSON from LLM responses, handling common markdown wrapping.
    LLMs often wrap JSON in ```json ... ``` code blocks despite instructions.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Raw LLM output: {text[:500]}")
        return None


# =============================================================================
# generate_campaign_email() — Full Email Content Generation
# =============================================================================
async def generate_campaign_email(campaign: Any) -> dict[str, str]:
    """
    Generate a complete promotional email (subject, text body, HTML body)
    for a social campaign.
    """
    system_prompt = (
        "You are a marketing email copywriter for QuantCAI, an enterprise AI tech brand. "
        "Your output MUST be a valid JSON object with EXACTLY 5 keys: "
        "subject, headline, subheadline, body_copy, cta_text. "
        "No markdown fences. Return ONLY the JSON."
    )

    prompt = f"""Write a promotional email based on this campaign context:

Campaign Base Content: {campaign.baseCaption}

Return a JSON object with:
1. "subject": A catchy email subject line
2. "headline": A strong 2-5 word headline
3. "subheadline": A short sentence elaborating on the headline
4. "body_copy": 2-3 sentences of persuasive body copy selling the service. DO NOT include HTML.
5. "cta_text": Short text for a button (e.g. "Get Started")"""

    text = await _call_openrouter(
        prompt,
        system_prompt=system_prompt,
    )

    parsed = _parse_json_response(text)
    
    # Defaults in case of failure or missing keys
    content = {
        "subject": "Transform your business with QuantCAI",
        "headline": "Unlock Enterprise AI",
        "subheadline": "Automate your workflows today.",
        "body_copy": "Check out our latest automation tools to help you scale.",
        "cta_text": "Learn More"
    }

    if parsed and isinstance(parsed, dict):
        content.update(parsed)
        
    # Prepare template variables
    campaign_url = "https://quantcai.in/"
    
    # Very basic HTML layout
    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333; padding: 20px;">
        <h2 style="text-align: center; color: #1a1a1a;">{content['headline']}</h2>
        <p style="text-align: center; font-size: 1.1em; color: #666;">{content['subheadline']}</p>
        <div style="text-align: center; margin: 20px 0;">
            <img src="{campaign.mediaUrl}" alt="Campaign Media" style="max-width: 100%; border-radius: 8px;" />
        </div>
        <p style="line-height: 1.6;">{content['body_copy']}</p>
        <div style="text-align: center; margin-top: 30px;">
            <a href="{campaign_url}" style="display: inline-block; padding: 14px 28px; background-color: #6366f1; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">{content['cta_text']}</a>
        </div>
        <p style="font-size: 0.8em; color: #999; margin-top: 40px; text-align: center;">You're receiving this because you're part of the QuantCAI community. <a href="#">Unsubscribe</a></p>
    </div>
    """

    return {
        "subject": content["subject"],
        "bodyText": f"{content['headline']}\n\n{content['body_copy']}\n\n{content['cta_text']}: {campaign_url}",
        "bodyHtml": body_html,
    }


# =============================================================================
# generate_campaign_variation() — AI Rewrite for Social Campaigns
# =============================================================================
async def generate_campaign_variation(base_caption: str) -> str:
    """
    Generate a unique variation of a base campaign caption.
    """
    prompt = f"""Rewrite the following base social media caption to create a unique, engaging variation. 
Maintain the core message, links, and any key hashtags, but change the hook, phrasing, and emojis to keep the content fresh for a new post.

Base Caption:
{base_caption}

Return ONLY the new caption text. No intro, no quotes around it."""

    text = await _call_openrouter(prompt)
    return text if text and len(text) > 10 else base_caption
