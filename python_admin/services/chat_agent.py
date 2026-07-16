"""
=============================================================================
QuantCAI — AI Chatbot Command Center (LLM Tool Calling Agent)
=============================================================================
Implements the admin-side AI chatbot with OpenRouter's function calling
(tool calling) capabilities. The chat model can autonomously execute backend
Python tools based on natural language queries.

Model: google/gemini-2.5-flash (via OpenRouter)

Available Tools:
  - search_products: Search the product catalog by name or ID
  - post_social_ad: Generate AI caption and post to FB/IG
  - send_email_campaign: Generate promotional email and blast to audience
  - bulk_import_products: Extract SPU codes from text and import from CJ
  - trigger_fulfillment: Trigger CJ order fulfillment for a pending order
  - get_order_status: Check CJ fulfillment status for an order
  - get_marketing_stats: Get platform statistics and recent marketing activity

The agent supports multi-turn tool calling: if the model requests a tool,
it's executed, and the result is fed back for the model to formulate its
final response. Supports up to 5 chained tool calls per conversation turn.

All HTTP calls are async with exponential backoff.
=============================================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
from loguru import logger
from prisma import Prisma
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from services.ai_service import generate_promotional_email, generate_social_caption

from services.email_service import send_email_blast
from services.social_service import post_to_facebook, post_to_instagram

# =============================================================================
# Constants
# =============================================================================
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# google/gemini-2.5-flash — Used for chatbot with tool calling capability
CHATBOT_MODEL = "google/gemini-2.5-flash"

# Maximum number of tool call → response loops per conversation turn
MAX_TOOL_LOOPS = 5

# Timeout for chatbot LLM calls
CHATBOT_TIMEOUT = httpx.Timeout(60.0, connect=15.0)

# =============================================================================
# System Prompt — Defines the chatbot's personality and capabilities
# =============================================================================
SYSTEM_PROMPT = """You are the QuantCAI AI Admin Assistant — an intelligent marketing and operations agent built into the QuantCAI Admin Dashboard.

Your capabilities:
1. **Product Management**: Search and query the product catalog
2. **Social Media Marketing**: Generate AI captions and post to Facebook/Instagram
3. **Email Marketing**: Generate promotional emails and send to the audience list

6. **Analytics**: Provide marketing and sales statistics

Rules:
- When asked to create an ad or email for a product, ALWAYS use the available tools
- If you don't know a product ID, use search_products first to find it
- Be concise, professional, and action-oriented
- When reporting results, include specific details (post IDs, email counts, etc.)
- If a tool fails, explain the error clearly and suggest alternatives"""


# =============================================================================
# Tool Definitions — OpenAI-compatible function calling schema
# =============================================================================
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the product database by keyword, product name, or ID. "
                "Returns matching products with their IDs, names, and prices."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — product name, keyword, or product ID",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "post_social_ad",
            "description": (
                "Generate an AI-powered high-converting caption and post the product "
                "to Facebook and/or Instagram with its images/video."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The database ID (cuid) of the product to advertise",
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform to post on",
                        "enum": ["FACEBOOK", "INSTAGRAM", "BOTH"],
                    },
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_campaign",
            "description": (
                "Generate a promotional email for the product using AI and "
                "send it to all subscribers in the audience database via Resend."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The database ID (cuid) of the product to promote",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_marketing_stats",
            "description": (
                "Get platform statistics: total products, orders, revenue, "
                "audience size, and recent marketing activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# =============================================================================
# Tool Executor — Routes tool calls to the appropriate backend function
# =============================================================================
async def execute_tool(
    name: str, args: dict[str, Any], prisma: Prisma
) -> str:
    """
    Execute a tool call from the LLM and return the result as a string.

    This is the bridge between the LLM's function calling and our backend
    services. Each tool maps to one or more service functions.

    Args:
        name: The tool function name requested by the LLM
        args: The arguments dict parsed from the LLM's function call
        prisma: The Prisma client instance (from app.state)

    Returns:
        A string result to feed back to the LLM
    """
    try:
        # --- search_products ---
        if name == "search_products":
            query = args.get("query", "")

            # Try exact ID match first
            product = await prisma.product.find_first(where={"id": query})
            if product:
                return (
                    f"Found exact product:\n"
                    f"  ID: {product.id}\n"
                    f"  Name: {product.productName}\n"
                    f"  Price: ${product.sellPrice}\n"
                    f"  Cost: ${product.costPrice}\n"
                    f"  Category: {product.categoryName}\n"
                    f"  Description: {product.description[:200]}..."
                )

            # Search by name (case-insensitive contains)
            products = await prisma.product.find_many(
                where={"productName": {"contains": query, "mode": "insensitive"}},
                take=5,
            )
            if not products:
                return f"No products found matching '{query}'"

            lines = [f"Found {len(products)} product(s):"]
            for p in products:
                lines.append(
                    f"  ID: {p.id} | {p.productName} | ${p.sellPrice} | {p.categoryName}"
                )
            return "\n".join(lines)

        # --- post_social_ad ---
        elif name == "post_social_ad":
            product_id = args.get("product_id", "")
            platform = args.get("platform", "BOTH")

            product = await prisma.product.find_unique(where={"id": product_id})
            if not product:
                return f"Error: Product with ID '{product_id}' not found."

            # Generate AI caption
            caption = await generate_social_caption(product)

            # Gather media (video-first priority)
            media_urls: list[str] = []
            if product.productVideo:
                media_urls.append(product.productVideo)
            if product.productImages:
                media_urls.extend(product.productImages)
            elif product.productImage:
                media_urls.append(product.productImage)

            # Create draft record
            post = await prisma.socialpost.create(
                data={
                    "productId": product.id,
                    "platform": platform,
                    "type": "CHAT_BOT",
                    "caption": caption,
                    "mediaUrls": media_urls,
                    "scheduledAt": datetime.now(),
                    "status": "DRAFT",
                }
            )

            # Post to platforms
            fb_id, ig_id = None, None
            errors: list[str] = []

            if platform in ("FACEBOOK", "BOTH"):
                try:
                    fb_id = await post_to_facebook(message=caption, media_urls=media_urls)
                except Exception as e:
                    errors.append(f"FB: {e}")

            if platform in ("INSTAGRAM", "BOTH"):
                try:
                    ig_id = await post_to_instagram(message=caption, media_urls=media_urls)
                except Exception as e:
                    errors.append(f"IG: {e}")

            is_success = fb_id is not None or ig_id is not None

            # Update record
            await prisma.socialpost.update(
                where={"id": post.id},
                data={
                    "status": "POSTED" if is_success else "FAILED",
                    "postedAt": datetime.now() if is_success else None,
                    "fbPostId": fb_id,
                    "igPostId": ig_id,
                    "errorLog": " | ".join(errors) if errors else None,
                },
            )

            result = f"Social post created for '{product.productName}' → {platform}\n"
            result += f"Caption: {caption[:100]}...\n"
            result += f"Status: {'POSTED ✓' if is_success else 'FAILED ✗'}"
            if fb_id:
                result += f"\nFB Post ID: {fb_id}"
            if ig_id:
                result += f"\nIG Post ID: {ig_id}"
            if errors:
                result += f"\nErrors: {', '.join(errors)}"
            return result

        # --- send_email_campaign ---
        elif name == "send_email_campaign":
            product_id = args.get("product_id", "")
            product = await prisma.product.find_unique(where={"id": product_id})
            if not product:
                return f"Error: Product with ID '{product_id}' not found."

            # Generate email content
            email_content = await generate_promotional_email(product)
            subject = email_content.get("subject", "Special Offer")
            body_text = email_content.get("bodyText", "")
            body_html = email_content.get("bodyHtml", "")

            # Create campaign record
            campaign = await prisma.emailcampaign.create(
                data={
                    "productId": product.id,
                    "type": "CHAT_BOT",
                    "subject": subject,
                    "bodyText": body_text,
                    "bodyHtml": body_html,
                    "scheduledAt": datetime.now(),
                    "status": "DRAFT",
                }
            )

            # Send via Resend
            try:
                result_data = await send_email_blast(
                    subject=subject,
                    html_body=body_html,
                    text_body=body_text,
                    prisma=prisma,
                )
                is_success = result_data.get("success", False)
                recipient_count = result_data.get("count", 0)
                error_log = result_data.get("error")
            except Exception as e:
                is_success = False
                recipient_count = 0
                error_log = str(e)

            await prisma.emailcampaign.update(
                where={"id": campaign.id},
                data={
                    "status": "SENT" if is_success else "FAILED",
                    "sentAt": datetime.now() if is_success else None,
                    "recipientCount": recipient_count,
                    "errorLog": error_log,
                },
            )

            if is_success:
                return (
                    f"✓ Email campaign sent for '{product.productName}'\n"
                    f"Subject: {subject}\n"
                    f"Recipients: {recipient_count}"
                )
            return f"✗ Email campaign failed: {error_log}"


        # --- get_marketing_stats ---
        elif name == "get_marketing_stats":
            product_count = 0
            order_count = 0
            audience_count = await prisma.audience.count()

            total_revenue = 0

            # Recent marketing activity
            recent_posts = await prisma.socialpost.count(
                where={"status": "POSTED"}
            )
            recent_emails = await prisma.emailcampaign.count(
                where={"status": "SENT"}
            )

            return (
                f"Platform Statistics:\n"
                f"  Products: {product_count}\n"
                f"  Orders: {order_count}\n"
                f"  Total Revenue: ${total_revenue:,.2f}\n"
                f"  Audience Size: {audience_count}\n"
                f"  Social Posts (posted): {recent_posts}\n"
                f"  Email Campaigns (sent): {recent_emails}"
            )

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        logger.error(f"Tool execution error ({name}): {e}")
        return f"Error executing {name}: {str(e)}"


# =============================================================================
# Chat With Agent — Multi-turn Tool Calling Loop
# =============================================================================
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=15),
    stop=stop_after_attempt(2),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
async def _call_chatbot_llm(
    messages: list[dict], *, include_tools: bool = True
) -> dict:
    """Make a single LLM call to OpenRouter with tool definitions."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://quantcai.in",
        "X-Title": "QuantCAI Admin Chatbot",
    }

    payload: dict[str, Any] = {
        "model": CHATBOT_MODEL,
        "messages": messages,
    }
    if include_tools:
        payload["tools"] = TOOLS
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=CHATBOT_TIMEOUT) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def chat_with_agent(
    messages: list[dict[str, Any]], prisma: Prisma
) -> dict[str, str]:
    """
    Send a conversation to the AI chatbot and handle tool calling.

    This implements the full multi-turn tool calling loop:
    1. Send messages to OpenRouter with tool definitions
    2. If the model requests a tool call, execute it
    3. Feed the tool result back to the model
    4. Repeat until the model produces a text response (max MAX_TOOL_LOOPS)

    Args:
        messages: List of conversation messages [{"role": "user", "content": "..."}]
        prisma: The Prisma client instance (from app.state)

    Returns:
        Dict with 'role' and 'content' keys (the assistant's final response)
    """
    if not settings.openrouter_api_key:
        return {
            "role": "assistant",
            "content": "Error: OPENROUTER_API_KEY is not configured.",
        }

    # Prepend system prompt to the conversation
    current_messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + messages

    for loop_idx in range(MAX_TOOL_LOOPS):
        try:
            result = await _call_chatbot_llm(current_messages)
            message = result["choices"][0]["message"]

            # Check if the model wants to call tools
            if message.get("tool_calls"):
                # Add the assistant's tool-call message to context
                current_messages.append(message)

                # Execute each requested tool
                for tool_call in message["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])

                    logger.info(
                        f"Chatbot tool call [{loop_idx + 1}/{MAX_TOOL_LOOPS}]: "
                        f"{func_name}({json.dumps(func_args)[:200]})"
                    )

                    tool_result = await execute_tool(func_name, func_args, prisma)

                    logger.info(f"Tool result ({func_name}): {tool_result[:200]}...")

                    # Add tool result to conversation context
                    current_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": str(tool_result),
                        }
                    )

                # Loop back to get the model's response with tool results
                continue
            else:
                # Model produced a text response — we're done
                return {
                    "role": "assistant",
                    "content": message.get("content", ""),
                }

        except Exception as e:
            logger.error(f"Chatbot error on loop {loop_idx + 1}: {e}")
            return {
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {str(e)}",
            }

    # Exhausted all tool loops
    return {
        "role": "assistant",
        "content": (
            "I've reached the maximum number of tool calls for this request. "
            "The actions have been executed — please check the dashboard for results."
        ),
    }
