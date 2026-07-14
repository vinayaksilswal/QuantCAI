"""
=============================================================================
QuantCAI — OpenRouter LLM Client (AI Copy & Marketing Asset Generation)
=============================================================================
Integrates with OpenRouter's API at https://openrouter.ai/api/v1/chat/completions
using the tencent/hy3:free model for marketing copy generation.

Key Functions:
  - generate_marketing_assets(): JSON output with instagram_caption,
    email_subject, and email_body (HTML)
  - generate_social_caption(): Standalone social caption generation
  - generate_promotional_email(): Full email content (subject, text, HTML)
  - generate_product_copy(): AI rewrite of raw CJ product data into
    premium e-commerce copy

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
# generate_marketing_assets() — The All-In-One Marketing Generator
# =============================================================================
async def generate_marketing_assets(product_data: dict[str, Any]) -> dict[str, str]:
    """
    Generate a complete marketing asset package for a product using AI.

    Uses a strict system prompt forcing JSON output containing:
    - instagram_caption: High-converting IG/FB caption with emojis and CTA
    - email_subject: Compelling email subject line
    - email_body: Full HTML email body with inline CSS, responsive design,
                  product image, and CTA button

    Args:
        product_data: Dict with keys: productName, sellPrice, originalPrice,
                      description, highlights, categoryName, productImage,
                      tagline, id (for product URL)

    Returns:
        Dict with keys: instagram_caption, email_subject, email_body
        Falls back to sensible defaults if AI generation fails.
    """
    product_name = product_data.get("productName", "Product")
    sell_price = product_data.get("sellPrice", 0)
    original_price = product_data.get("originalPrice", 0)
    description = product_data.get("description", "")
    highlights = product_data.get("highlights", [])
    tagline = product_data.get("tagline", "")
    product_image = product_data.get("productImage", "")
    product_id = product_data.get("id", "")
    product_url = f"https://quantcai.in/product/{product_id}"

    system_prompt = (
        "You are an expert direct-response copywriter for QuantCAI, a cutting-edge Enterprise AI automation and agents platform. "
        "You generate technical yet accessible marketing assets that convert. Your output MUST be a valid JSON object with EXACTLY these keys: "
        "instagram_caption, email_subject, email_body. No markdown fences, no "
        "explanations — just the raw JSON object."
    )

    prompt = f"""Generate a complete marketing asset package for this product:

Product Name: {product_name}
Price: ${sell_price} (was ${original_price})
Tagline: {tagline}
Description: {description[:500]}
Highlights: {', '.join(highlights) if isinstance(highlights, list) else highlights}
Product Image URL: {product_image}
Product URL: {product_url}

Return a JSON object with exactly these keys:
1. "instagram_caption": An engaging, high-converting Instagram caption (under 150 words). Include relevant emojis, a strong CTA, and 3-5 hashtags. Tone: professional, cutting-edge, tech-focused.
2. "email_subject": A catchy email subject line (under 60 chars) that drives opens.
3. "email_body": A complete HTML email body with inline CSS styling. Requirements:
   - Responsive design (max-width: 600px, centered)
   - Modern sans-serif font (Arial/Helvetica)
   - Include the product image using src="{product_image}"
   - Bold product name and price with strikethrough original price
   - Highlight key benefits
   - Prominent CTA button linking to {product_url}
   - Professional color scheme (dark text, accent buttons)
   - Unsubscribe placeholder text at bottom"""

    text = await _call_openrouter(
        prompt,
        json_response=True,
        system_prompt=system_prompt,
    )

    parsed = _parse_json_response(text)

    if parsed and all(
        k in parsed for k in ("instagram_caption", "email_subject", "email_body")
    ):
        # Replace image placeholder if present
        if product_image and "[PRODUCT_IMAGE_URL]" in parsed.get("email_body", ""):
            parsed["email_body"] = parsed["email_body"].replace(
                "[PRODUCT_IMAGE_URL]", product_image
            )
        logger.info(f"✓ Marketing assets generated for: {product_name}")
        return parsed

    # Fallback defaults if AI generation fails
    logger.warning(f"Marketing asset generation failed for {product_name}, using defaults")
    return {
        "instagram_caption": (
            f"✨ Discover {product_name} — {tagline or 'Transform your workflows.'}\n\n"
            f"💫 Now only ${sell_price} (was ${original_price})\n\n"
            f"🛒 Learn more at quantcai.in\n\n"
            f"#QuantCAI #EnterpriseAI #Automation #AI #Tech"
        ),
        "email_subject": f"✨ {product_name} — Now ${sell_price}",
        "email_body": f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <h2 style="text-align: center; color: #1a1a1a;">{product_name}</h2>
    <img src="{product_image}" alt="{product_name}" style="max-width: 100%; border-radius: 8px;" />
    <p>{description[:300]}</p>
    <p style="font-size: 1.2em; font-weight: bold;">
        Now <span style="color: #e74c3c;">${sell_price}</span>
        <span style="text-decoration: line-through; color: #999;">${original_price}</span>
    </p>
    <a href="{product_url}" style="display: inline-block; padding: 14px 28px; background-color: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">Order Now →</a>
    <p style="font-size: 0.8em; color: #999; margin-top: 24px;">You're receiving this because you're part of the QuantCAI community. <a href="#">Unsubscribe</a></p>
</div>""",
    }


# =============================================================================
# generate_social_caption() — Standalone Social Caption
# =============================================================================
async def generate_social_caption(product: Any) -> str:
    """
    Generate a high-converting, viral social media caption with a strong hook, 
    benefits-driven copy, and clear CTA.

    Args:
        product: Prisma Product model instance

    Returns:
        The generated caption string
    """
    save_pct = round((1 - float(product.sellPrice) / (
        product.originalPrice if (getattr(product, 'originalPrice', None) and product.originalPrice > product.sellPrice)
        else float(product.sellPrice) * 1.45
    )) * 100)

    prompt = f"""Write a high-converting, viral social media caption for Instagram and Facebook for this product:

Product Name: {product.productName}
Price: ${product.sellPrice}
Save: {save_pct}% off retail
Category: {product.categoryName}
Tagline: {product.tagline or ''}
Description: {product.description[:500] if product.description else ''}
Highlights: {', '.join(product.highlights) if product.highlights else ''}

Requirements:
1. Start with a STRONG hook (bold question, surprising fact, or scroll-stopping statement).
2. Build desire in 2-3 lines — mention a real benefit, pain point solved, or transformation.
3. Include social proof (e.g. "Trusted by top enterprises", "rated 4.9/5").
4. Include the price and savings clearly.
5. Strong CTA: "Learn more at quantcai.in — link in bio!"
6. End with 15-20 niche-targeted hashtags (mix large + small audiences).
7. Use emojis naturally — 1-2 per paragraph max.
8. Confident tech brand voice. NOT desperate or generic.
9. Total: 180-250 words including hashtags.
10. Return ONLY the caption. No intro text."""

    text = await _call_openrouter(prompt)
    if text and len(text) > 50:
        return text

    # Crafted fallback
    return (
        f"✨ This is the AI upgrade you've been putting off.\n\n"
        f"Introducing the {product.productName} — enterprise-grade AI automation, "
        f"now available for your business workflows.\n\n"
        f"💫 Join top enterprises who made this their daily advantage.\n"
        f"⭐ Rated 4.9/5 with verified ROI in 2–4 weeks.\n\n"
        f"🔥 Limited-time: ${product.sellPrice} (save {save_pct}% off retail)\n"
        f"🚚 Instant deployment\n"
        f"✅ 30-day money-back guarantee\n\n"
        f"👉 Learn more at quantcai.in — link in bio!\n\n"
        f"#QuantCAI #EnterpriseAI #Automation #AIAgents #TechInnovation "
        f"#FutureOfWork #MachineLearning #BusinessAutomation #Productivity "
        f"#TechTrends #DigitalTransformation #AI #Software "
        f"#Innovation #SmartTech #WorkSmarter #QuantCAItech"
    )


# =============================================================================
# generate_promotional_email() — Full Email Content Generation
# =============================================================================
async def generate_promotional_email(product: Any) -> dict[str, str]:
    """
    Generate a complete promotional email (subject, text body, HTML body)
    for a product. Used by the scheduler and manual email creation flows.

    Args:
        product: Prisma Product model instance

    Returns:
        Dict with keys: subject, bodyText, bodyHtml
    """
    original_price = (
        product.originalPrice
        if product.originalPrice > product.sellPrice
        else product.sellPrice
    )
    product_url = f"https://quantcai.in/product/{product.id}"
    
    # Initialize Jinja environment
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email_templates")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )

    system_prompt = (
        "You are a marketing email copywriter for QuantCAI, an enterprise AI tech brand. "
        "Your output MUST be a valid JSON object with EXACTLY 5 keys: "
        "subject, headline, subheadline, body_copy, cta_text, template_type. "
        "template_type MUST be one of: 'product_spotlight', 'sale_promotion', 'brand_highlight'. "
        "No markdown fences. Return ONLY the JSON."
    )

    prompt = f"""Write a promotional email for this product:

Product Name: {product.productName}
Price: ${product.sellPrice}
Original Price: ${original_price}
Category: {product.categoryName}
Tagline: {product.tagline or ''}
Description: {product.description[:400] if product.description else ''}
Highlights: {', '.join(product.highlights) if product.highlights else ''}
Product URL: {product_url}

Return a JSON object with:
1. "subject": A catchy email subject line
2. "headline": A strong 2-5 word headline (e.g. "Season's Must-Haves")
3. "subheadline": A short sentence elaborating on the headline
4. "body_copy": 2-3 sentences of persuasive body copy selling the product. DO NOT include HTML.
5. "cta_text": Short text for a button (e.g. "Order Now")
6. "template_type": Pick ONE based on the product vibe: 'product_spotlight', 'sale_promotion', or 'brand_highlight'."""

    text = await _call_openrouter(
        prompt,
        system_prompt=system_prompt,
    )

    parsed = _parse_json_response(text)
    
    # Defaults in case of failure or missing keys
    content = {
        "subject": f"Featured: {product.productName}",
        "headline": "New Arrival",
        "subheadline": "Discover the latest in premium wellness.",
        "body_copy": f"Check out {product.productName} for ${product.sellPrice}.",
        "cta_text": "Shop Now",
        "template_type": "product_spotlight"
    }

    if parsed and isinstance(parsed, dict):
        content.update(parsed)
        
    # Validate template type
    valid_templates = ['product_spotlight', 'sale_promotion', 'brand_highlight']
    if content['template_type'] not in valid_templates:
        content['template_type'] = 'product_spotlight'
        
    # Prepare template variables
    template_vars = {
        "subject": content["subject"],
        "headline": content["headline"],
        "subheadline": content["subheadline"],
        "body_copy": content["body_copy"],
        "cta_text": content["cta_text"],
        "product_name": product.productName,
        "product_price": product.sellPrice,
        "product_url": product_url,
        "product_image": product.productImage or "https://via.placeholder.com/600x400"
    }
    
    try:
        template = env.get_template(f"{content['template_type']}.html")
        body_html = template.render(**template_vars)
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        # Very basic fallback
        body_html = f"<p>{content['body_copy']}</p><p><a href='{product_url}'>{content['cta_text']}</a></p>"

    return {
        "subject": content["subject"],
        "bodyText": f"{content['headline']}\\n\\n{content['body_copy']}\\n\\n{content['cta_text']}: {product_url}",
        "bodyHtml": body_html,
    }


# =============================================================================
# generate_product_copy() — AI Rewrite for CJ Product Imports
# =============================================================================
async def generate_product_copy(
    title: str, description: str, pid: str | None = None
) -> dict[str, Any]:
    """
    Take raw CJ product data and rewrite it into premium e-commerce copy.

    Generates:
    - title: Concise premium product name (max 6 words)
    - description: 2-paragraph HTML sales description
    - highlights: Array of 4 short benefit bullet points
    - tagline: 3-6 word hero tagline

    Args:
        title: Raw product title from CJ
        description: Raw product description from CJ
        pid: Optional CJ product ID for logging

    Returns:
        Dict with keys: title, description, highlights, tagline
    """
    system_prompt = (
        "You are an expert direct-response tech copywriter for QuantCAI, a cutting-edge Enterprise AI automation and agents platform. "
        "Your output MUST be a valid JSON object. No markdown fences, no explanations."
    )

    prompt = f"""Rewrite this raw supplier product data into premium e-commerce copy:

Raw Title: {title}
Raw Description: {description[:800]}

Return a valid JSON object with these keys EXACTLY:
"title": A concise, premium-sounding product name (max 6 words). Remove cheap buzzwords like 'dropshipping' or 'wholesale'.
"description": A compelling 2-paragraph sales description focusing on enterprise benefits and ROI. Use basic HTML (<p> and <strong>).
"highlights": An array of exactly 4 short, punchy bullet points (strings) highlighting key benefits.
"tagline": A short, 3-6 word catchy tagline for the hero section."""

    text = await _call_openrouter(
        prompt,
        json_response=True,
        system_prompt=system_prompt,
    )

    parsed = _parse_json_response(text)

    if parsed and "title" in parsed:
        logger.info(f"✓ Product copy rewritten: {title[:50]} → {parsed['title']}")
        return parsed

    # Fallback if AI fails
    logger.warning(f"Product copy generation failed for '{title[:50]}', using defaults")
    return {
        "title": title,
        "description": description or "Premium wellness product.",
        "highlights": [
            "Clinically tested",
            "Dermatologist recommended",
            "Free shipping",
            "Results in weeks",
        ],
        "tagline": "Transform your routine.",
    }


# =============================================================================
# generate_social_post() — Legacy sync-compatible wrapper
# =============================================================================
async def generate_social_post(
    product_name: str, highlights: list[str], price: float
) -> str:
    """
    Generate a social media caption from basic product info.
    Legacy compatibility wrapper — prefer generate_social_caption() with
    full product object when possible.
    """
    prompt = f"""Write an engaging, high-converting social media caption (for Instagram and Facebook):
Product Name: {product_name}
Price: ${price}
Key Highlights: {', '.join(highlights)}

Tone: premium, wellness-focused, exciting. Include relevant emojis and a CTA. No hashtags."""

    text = await _call_openrouter(prompt)
    return text or f"Check out our {product_name}! Only ${price}."
