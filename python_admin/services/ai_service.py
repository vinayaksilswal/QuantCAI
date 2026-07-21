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
        "You are an elite B2B enterprise SaaS marketing copywriter for QuantCAI, a premium AI automation brand. "
        "Your goal is to drive high-value organic conversions, highlighting ROI, scalability, and seamless integration. "
        "Your output MUST be a valid JSON object with EXACTLY 5 keys: "
        "subject, headline, subheadline, body_copy, cta_text. "
        "No markdown fences. Return ONLY the JSON."
    )

    prompt = f"""Write a promotional email based on this campaign context:

Campaign Base Content: {campaign.baseCaption}

Return a JSON object with:
1. "subject": A high-converting, curiosity-driven email subject line
2. "headline": A strong 2-5 word headline focusing on business value
3. "subheadline": A short sentence elaborating on the headline and urgency
4. "body_copy": 2-3 sentences of persuasive body copy selling the service. Focus on pain points and solutions. DO NOT include HTML.
5. "cta_text": Action-oriented text for a button (e.g. "Scale Your Business", "Start Free Trial")"""

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
        
    # Prepare template variables (with UTM tracking)
    campaign_url = f"https://quantcai.in/?utm_source=auto_email&utm_medium=organic&utm_campaign=ai_loop_{campaign.id}"
    
    # Premium Enterprise HTML Layout
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f6; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px; text-align: center; background-color: #0f172a;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Quant<span style="color: #6366f1;">CAI</span></h1>
                            </td>
                        </tr>
                        <!-- Hero Section -->
                        <tr>
                            <td style="padding: 30px 40px; text-align: center;">
                                <h2 style="margin: 0 0 15px 0; color: #1e293b; font-size: 24px; font-weight: 700;">{content['headline']}</h2>
                                <p style="margin: 0; color: #64748b; font-size: 18px; line-height: 1.5;">{content['subheadline']}</p>
                            </td>
                        </tr>
                        <!-- Media -->
                        <tr>
                            <td style="padding: 0 40px;">
                                <img src="{campaign.mediaUrl}" alt="QuantCAI Showcase" style="width: 100%; max-width: 520px; height: auto; border-radius: 8px; border: 1px solid #e2e8f0; display: block; margin: 0 auto;" />
                            </td>
                        </tr>
                        <!-- Body Copy -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <p style="margin: 0; color: #334155; font-size: 16px; line-height: 1.6;">{content['body_copy']}</p>
                            </td>
                        </tr>
                        <!-- CTA Button -->
                        <tr>
                            <td style="padding: 10px 40px 40px; text-align: center;">
                                <a href="{campaign_url}" style="display: inline-block; padding: 16px 36px; background-color: #4f46e5; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; transition: background-color 0.2s;">{content['cta_text']}</a>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                <p style="margin: 0; color: #94a3b8; font-size: 13px;">Enterprise AI Infrastructure for the Modern Web.</p>
                                <p style="margin: 10px 0 0; color: #94a3b8; font-size: 12px;">You're receiving this because you're part of the QuantCAI community. <a href="https://quantcai.in/unsubscribe" style="color: #64748b; text-decoration: underline;">Unsubscribe</a></p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
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
    prompt = f"""Rewrite the following base social media caption to create a highly engaging, professional yet energetic variation for an enterprise B2B audience.
The goal is to drive organic engagement, establish authority, and compel users to click the link.
Use modern business-friendly formatting, targeted high-value hashtags (#EnterpriseAI, #Automation, #SaaS), and strategic emojis.
Appened this link at the end of the post (it includes UTM tracking): https://quantcai.in/?utm_source=auto_social&utm_medium=organic&utm_campaign=ai_loop

Base Caption:
{base_caption}

Return ONLY the new caption text. No intro, no quotes around it."""

    text = await _call_openrouter(prompt)
    return text if text and len(text) > 10 else base_caption

# =============================================================================
# generate_social_caption()
# =============================================================================
async def generate_social_caption(product: Any) -> str:
    """
    Generate an engaging social media caption for a product.
    """
    prompt = f"""Write an engaging social media caption for this product:
Product Name: {product.productName}
Description: {product.description}
Price: ${product.sellPrice}

Keep it exciting, use emojis, and include relevant hashtags.
Return ONLY the caption text."""
    
    text = await _call_openrouter(prompt)
    return text if text and len(text) > 10 else f"Check out our new {product.productName}! Available now for just ${product.sellPrice}. 🚀 #newarrival #musthave"

# =============================================================================
# generate_promotional_email()
# =============================================================================
async def generate_promotional_email(product: Any) -> dict[str, str]:
    """
    Generate a promotional email for a product.
    """
    system_prompt = (
        "You are a marketing email copywriter. "
        "Your output MUST be a valid JSON object with EXACTLY 5 keys: "
        "subject, headline, subheadline, body_copy, cta_text. "
        "No markdown fences. Return ONLY the JSON."
    )

    prompt = f"""Write a promotional email for this product:
Product Name: {product.productName}
Description: {product.description}
Price: ${product.sellPrice}

Return a JSON object with:
1. "subject": A catchy email subject line
2. "headline": A strong 2-5 word headline
3. "subheadline": A short sentence elaborating on the headline
4. "body_copy": 2-3 sentences of persuasive body copy selling the product. DO NOT include HTML.
5. "cta_text": Short text for a button (e.g. "Buy Now")"""

    text = await _call_openrouter(prompt, system_prompt=system_prompt, json_response=True)
    parsed = _parse_json_response(text)
    
    content = {
        "subject": f"Special Offer: {product.productName}",
        "headline": "New Arrival!",
        "subheadline": f"Get the {product.productName} today.",
        "body_copy": str(product.description)[:100] + "..." if product.description else "Check out our newest addition.",
        "cta_text": "Shop Now"
    }

    if parsed and isinstance(parsed, dict):
        content.update(parsed)

    product_url = "https://quantcai.in/" # default url
    
    img_url = ""
    if hasattr(product, 'productImage') and product.productImage:
        img_url = product.productImage
    elif hasattr(product, 'productImages') and product.productImages and len(product.productImages) > 0:
        img_url = product.productImages[0]

    img_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{img_url}" alt="{product.productName}" style="max-width: 100%; border-radius: 8px;" /></div>' if img_url else ""

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f6; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px; text-align: center; background-color: #0f172a;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Quant<span style="color: #6366f1;">CAI</span></h1>
                            </td>
                        </tr>
                        <!-- Hero Section -->
                        <tr>
                            <td style="padding: 30px 40px; text-align: center;">
                                <h2 style="margin: 0 0 15px 0; color: #1e293b; font-size: 24px; font-weight: 700;">{content['headline']}</h2>
                                <p style="margin: 0; color: #64748b; font-size: 18px; line-height: 1.5;">{content['subheadline']}</p>
                            </td>
                        </tr>
                        <!-- Media -->
                        <tr>
                            <td style="padding: 0 40px;">
                                {img_html}
                            </td>
                        </tr>
                        <!-- Body Copy -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <p style="margin: 0; color: #334155; font-size: 16px; line-height: 1.6;">{content['body_copy']}</p>
                            </td>
                        </tr>
                        <!-- CTA Button -->
                        <tr>
                            <td style="padding: 10px 40px 40px; text-align: center;">
                                <a href="{product_url}" style="display: inline-block; padding: 16px 36px; background-color: #4f46e5; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">{content['cta_text']}</a>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                <p style="margin: 0; color: #94a3b8; font-size: 13px;">Enterprise Quantum Security & Simulation Infrastructure.</p>
                                <p style="margin: 10px 0 0; color: #94a3b8; font-size: 12px;">You're receiving this because you're part of the QuantCAI community. <a href="https://quantcai.in/unsubscribe" style="color: #64748b; text-decoration: underline;">Unsubscribe</a></p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return {
        "subject": content["subject"],
        "bodyText": f"{content['headline']}\n\n{content['body_copy']}\n\n{content['cta_text']}: {product_url}",
        "bodyHtml": body_html,
    }


# =============================================================================
# arXiv Research → Social Content Generation
# =============================================================================
# These functions transform academic paper abstracts into platform-ready
# social media content for the autonomous arXiv newsroom pipeline.
# =============================================================================

ARXIV_X_SYSTEM_PROMPT = """You are a senior quantum computing developer advocate writing for X (Twitter).
Your audience is Python developers, quantum researchers, and Qiskit users.

RULES:
- Write exactly 3 posts for an X thread. Each post MUST be under 280 characters.
- Post 1: Hook — summarize what the paper discovered in a punchy, engaging way. Use an emoji opener.
- Post 2: Technical implications — what this means for Python/Qiskit developers. Include a hypothetical code snippet or library reference if relevant.
- Post 3: Call-to-action — direct readers to explore this concept on QuantCAI. Use the CTA link provided.
- Be technically accurate but accessible. No hype or buzzwords.
- Include 3-5 relevant hashtags separately.

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "post_1": "...",
  "post_2": "...",
  "post_3": "...",
  "hashtags": ["#Quantum", "#Qiskit", ...]
}"""

ARXIV_LINKEDIN_SYSTEM_PROMPT = """You are a cybersecurity thought leader writing for LinkedIn.
Your audience is CISOs, VP of Engineering, compliance officers, and DevSecOps leaders.

RULES:
- Write a professional, risk-focused executive summary (max 3000 characters).
- Frame the research around the NSA CNSA 2.0 mandate (PQC in all new software by 2030, full replacement by 2033).
- Emphasize the shrinking timeline for Post-Quantum Cryptography (PQC) migration.
- Reference the average data breach cost ($4.44M) and the regulatory implications.
- End with a clear call-to-action to assess cryptographic posture using QuantCAI's PQC scanner at https://quantcai.in/pqc-scanner
- Include 3-5 professional hashtags separately.
- Do NOT use emojis. Use professional tone throughout.

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "body": "...",
  "hashtags": ["#PostQuantumCryptography", "#CyberSecurity", ...]
}"""


def _classify_paper_category(title: str, abstract: str) -> str:
    """Classify a paper as 'quantum' or 'cybersecurity' based on keywords."""
    text = (title + " " + abstract).lower()
    crypto_keywords = {
        "cryptograph", "post-quantum", "pqc", "lattice-based", "ml-kem", "ml-dsa",
        "slh-dsa", "nist", "rsa", "ecc", "key exchange", "digital signature",
        "encryption", "tls", "certificate", "vulnerability", "cybersecurity",
        "shor's algorithm", "factoring", "key encapsulation", "hash-based",
    }
    for kw in crypto_keywords:
        if kw in text:
            return "cybersecurity"
    return "quantum"


def _build_arxiv_cta_link(category: str, arxiv_id: str) -> str:
    """Build a trackable CTA link based on the paper's category."""
    base = "https://quantcai.in"
    utm = f"utm_source=arxiv_newsroom&utm_medium=social&utm_campaign={arxiv_id}"
    if category == "cybersecurity":
        return f"{base}/pqc-scanner?{utm}"
    return f"{base}/circuit-builder?{utm}"


async def generate_arxiv_x_thread(
    title: str, abstract: str, arxiv_id: str, cta_link: str
) -> dict:
    """
    Generate a 3-post X thread from an arXiv paper abstract.

    Returns:
        Dict with keys: post_1, post_2, post_3, hashtags
    """
    prompt = f"""Paper Title: {title}
Paper ID: {arxiv_id}
Abstract: {abstract}

CTA Link to include in post 3: {cta_link}"""

    text = await _call_openrouter(
        prompt,
        system_prompt=ARXIV_X_SYSTEM_PROMPT,
    )

    parsed = _parse_json_response(text)
    if parsed and isinstance(parsed, dict):
        return {
            "post_1": str(parsed.get("post_1", ""))[:280],
            "post_2": str(parsed.get("post_2", ""))[:280],
            "post_3": str(parsed.get("post_3", ""))[:280],
            "hashtags": parsed.get("hashtags", ["#Quantum", "#QuantCAI"]),
        }

    # Fallback if LLM fails
    return {
        "post_1": f"🔬 New research: {title[:200]}",
        "post_2": f"Read the full paper: https://arxiv.org/abs/{arxiv_id}",
        "post_3": f"Explore quantum concepts interactively → {cta_link}",
        "hashtags": ["#Quantum", "#Research", "#QuantCAI"],
    }


async def generate_arxiv_linkedin_post(
    title: str, abstract: str, arxiv_id: str, cta_link: str
) -> dict:
    """
    Generate a LinkedIn executive summary from an arXiv paper abstract.

    Returns:
        Dict with keys: body, hashtags
    """
    prompt = f"""Paper Title: {title}
Paper ID: {arxiv_id}
Abstract: {abstract}

CTA Link: {cta_link}"""

    text = await _call_openrouter(
        prompt,
        system_prompt=ARXIV_LINKEDIN_SYSTEM_PROMPT,
    )

    parsed = _parse_json_response(text)
    if parsed and isinstance(parsed, dict):
        return {
            "body": str(parsed.get("body", ""))[:3000],
            "hashtags": parsed.get("hashtags", ["#PostQuantumCryptography", "#CyberSecurity"]),
        }

    # Fallback if LLM fails
    category = _classify_paper_category(title, abstract)
    return {
        "body": (
            f"New research published on arXiv highlights critical developments "
            f"in {'post-quantum cryptography' if category == 'cybersecurity' else 'quantum computing'}.\n\n"
            f'"{title}"\n\n'
            f"Organizations preparing for the NSA CNSA 2.0 mandate should take note. "
            f"Assess your cryptographic posture at {cta_link}"
        ),
        "hashtags": ["#PostQuantumCryptography", "#CyberSecurity", "#CNSA2"],
    }


async def generate_arxiv_content(
    title: str, abstract: str, arxiv_id: str
) -> dict:
    """
    Full pipeline: Generate both X thread and LinkedIn post from an arXiv paper.

    Returns:
        Dict with keys: category, cta_link, x_thread, linkedin_post
    """
    category = _classify_paper_category(title, abstract)
    cta_link = _build_arxiv_cta_link(category, arxiv_id)

    x_thread = await generate_arxiv_x_thread(title, abstract, arxiv_id, cta_link)
    linkedin_post = await generate_arxiv_linkedin_post(title, abstract, arxiv_id, cta_link)

    return {
        "category": category,
        "cta_link": cta_link,
        "x_thread": x_thread,
        "linkedin_post": linkedin_post,
    }
