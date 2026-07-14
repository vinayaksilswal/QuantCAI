"""
=============================================================================
QuantCAI — CJ Dropshipping API v2 Client
=============================================================================
Handles the complete autonomous supply chain lifecycle:

1. AUTHENTICATION: Token caching with autonomous refresh via
   /api2.0/v1/authentication/refreshAccessToken

2. BULK SPU IMPORTER: Accepts raw text, extracts CJ SPU codes via regex,
   queries /api2.0/v1/product/query for each to fetch high-res variants
   and videoList arrays.

3. DYNAMIC PRICING ENGINE: On import, calculates:
   - Base Cost = CJ Cost + $15
   - Retail Price = Base Cost × 2.0
   - Strikethrough = Base Cost × 3.0

4. ZERO-TOUCH FULFILLMENT: Calls /api2.0/v1/shopping/order/createOrderV2
   with payType=2 (hardcoded) to enforce automated wallet balance deduction.

All HTTP calls use httpx.AsyncClient with tenacity exponential backoff.
=============================================================================
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
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
CJ_BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
TOKEN_FILE = ".cj_token.json"

# Shared timeout configuration for all CJ API calls
CJ_TIMEOUT = httpx.Timeout(20.0, connect=10.0)


# =============================================================================
# Token Cache — File-based persistence for access token
# =============================================================================
def _load_cached_token() -> str | None:
    """
    Load the CJ access token from the local cache file.
    Returns None if the file doesn't exist, is corrupt, or the token
    is within 10 minutes of expiry (to prevent mid-request expiration).
    """
    try:
        if not os.path.exists(TOKEN_FILE):
            return None

        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)

        expiry_str: str | None = data.get("expiry")
        token: str | None = data.get("token")

        if not token or not expiry_str:
            return None

        # Parse the expiry timestamp from CJ's format
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")

        # Reject token if within 10 minutes of expiry (safety buffer)
        if datetime.now() > expiry_date - timedelta(minutes=10):
            logger.info("CJ token cache expired or near-expiry, will refresh")
            return None

        return token
    except Exception as e:
        logger.warning(f"Failed to load cached CJ token: {e}")
        return None


def _save_token(token: str, expiry: str) -> None:
    """Persist the CJ access token and its expiry to disk."""
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": token, "expiry": expiry}, f)
        logger.debug("CJ token cached to disk")
    except Exception as e:
        logger.error(f"Failed to save CJ token to disk: {e}")


# =============================================================================
# HTTP Helpers — Retry-wrapped async HTTP calls
# =============================================================================
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=lambda retry_state: logger.warning(
        f"CJ API retry attempt {retry_state.attempt_number} after error"
    ),
)
async def _cj_post(url: str, payload: dict, headers: dict | None = None) -> dict:
    """POST to CJ API with exponential backoff retry."""
    async with httpx.AsyncClient(timeout=CJ_TIMEOUT) as client:
        response = await client.post(url, json=payload, headers=headers or {})
        response.raise_for_status()
        return response.json()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=lambda retry_state: logger.warning(
        f"CJ API retry attempt {retry_state.attempt_number} after error"
    ),
)
async def _cj_get(url: str, headers: dict) -> dict:
    """GET from CJ API with exponential backoff retry."""
    async with httpx.AsyncClient(timeout=CJ_TIMEOUT) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


# =============================================================================
# Authentication — Token Acquisition & Refresh
# =============================================================================
async def get_access_token(force_refresh: bool = False) -> dict[str, Any]:
    """
    Obtain a valid CJ access token, using cache when available.

    Flow:
    1. Check disk cache for a non-expired token (unless force_refresh=True).
    2. If cache miss, call getAccessToken with the API key.
    3. Cache the new token to disk.

    Returns:
        dict with keys: success, accessToken, mode, expiry
    """
    # Step 1: Try cached token (skip if forcing refresh)
    if not force_refresh:
        cached = _load_cached_token()
        if cached:
            logger.debug("Using cached CJ access token")
            return {"success": True, "accessToken": cached, "mode": "Live"}

    # Step 2: Validate API key exists
    if not settings.cj_api_key:
        logger.error("CJ_API_KEY not configured — cannot authenticate")
        return {"success": False, "error": "CJ_API_KEY missing from configuration"}

    # Step 3: Request new token
    url = f"{CJ_BASE_URL}/authentication/getAccessToken"
    try:
        data = await _cj_post(url, {"apiKey": settings.cj_api_key})
        if (
            data.get("code") == 200
            and data.get("data")
            and data["data"].get("accessToken")
        ):
            token = data["data"]["accessToken"]
            expiry = data["data"].get("accessTokenExpiryDate", "")
            _save_token(token, expiry)
            logger.info("✓ Successfully authenticated with CJ Dropshipping")
            return {
                "success": True,
                "accessToken": token,
                "mode": "Live",
                "expiry": expiry,
            }
        else:
            error_msg = data.get("message", "Unknown authentication error")
            logger.error(f"CJ auth failed: {error_msg}")
            return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"CJ authentication request failed: {e}")
        return {"success": False, "error": str(e)}


async def refresh_access_token() -> dict[str, Any]:
    """
    Autonomously refresh the CJ access token using the refreshAccessToken endpoint.

    This is called when the current token is expired or about to expire.
    The refreshAccessToken endpoint uses the existing (expired) token to get a new one.
    If refresh fails, falls back to a full re-authentication via getAccessToken.
    """
    cached = _load_cached_token()
    if not cached:
        # No cached token to refresh — do a full auth instead
        logger.info("No cached token for refresh, performing full authentication")
        return await get_access_token(force_refresh=True)

    url = f"{CJ_BASE_URL}/authentication/refreshAccessToken"
    headers = {
        "CJ-Access-Token": cached,
        "Content-Type": "application/json",
    }
    try:
        data = await _cj_post(url, {"accessToken": cached}, headers=headers)
        if (
            data.get("code") == 200
            and data.get("data")
            and data["data"].get("accessToken")
        ):
            new_token = data["data"]["accessToken"]
            new_expiry = data["data"].get("accessTokenExpiryDate", "")
            _save_token(new_token, new_expiry)
            logger.info("✓ CJ access token refreshed successfully")
            return {
                "success": True,
                "accessToken": new_token,
                "mode": "Live",
                "expiry": new_expiry,
            }
        else:
            # Refresh failed — fall back to full re-auth
            logger.warning("CJ token refresh failed, falling back to full auth")
            return await get_access_token(force_refresh=True)
    except Exception as e:
        logger.warning(f"CJ token refresh error: {e}, falling back to full auth")
        return await get_access_token(force_refresh=True)


async def _get_auth_headers() -> dict[str, str] | None:
    """
    Internal helper: get authenticated headers for CJ API calls.
    Handles token refresh automatically if the cached token is stale.
    Returns None if authentication fails entirely.
    """
    token_res = await get_access_token()
    if not token_res["success"]:
        # Try a forced refresh
        token_res = await refresh_access_token()
    if not token_res["success"]:
        logger.error("Cannot authenticate with CJ — all methods exhausted")
        return None
    return {
        "CJ-Access-Token": token_res["accessToken"],
        "Content-Type": "application/json",
    }


# =============================================================================
# Product Query — Fetch product details by PID/SPU
# =============================================================================
async def query_cj_product(pid: str) -> dict[str, Any]:
    """
    Query CJ Dropshipping for a single product by its PID (product ID).
    Returns the full product data including images, variants, and videoList.

    Args:
        pid: The CJ product identifier (PID or SPU code)

    Returns:
        dict with 'success' bool and 'product' data or 'error' message
    """
    headers = await _get_auth_headers()
    if not headers:
        return {"success": False, "error": "Cannot authenticate with CJ"}

    url = f"{CJ_BASE_URL}/product/query?pid={pid}"
    try:
        data = await _cj_get(url, headers)
        if data.get("code") == 200 and data.get("data"):
            logger.info(f"✓ CJ product fetched: {pid}")
            return {"success": True, "product": data["data"]}
        else:
            error_msg = data.get("message", "Product not found")
            logger.warning(f"CJ product query failed for {pid}: {error_msg}")
            return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"Error querying CJ product {pid}: {e}")
        return {"success": False, "error": str(e)}


async def get_product_variants(pid: str) -> dict[str, Any]:
    """
    Fetch all variants for a CJ product by PID.
    Variants include different sizes, colors, etc. with their own VIDs
    (variant IDs) needed for order fulfillment.

    Args:
        pid: The CJ product identifier

    Returns:
        dict with 'success' bool and 'variants' list or 'error' message
    """
    headers = await _get_auth_headers()
    if not headers:
        return {"success": False, "error": "Cannot authenticate with CJ"}

    url = f"{CJ_BASE_URL}/product/variant/queryByPid?pid={pid}"
    try:
        data = await _cj_get(url, headers)
        if data.get("code") == 200 and data.get("data"):
            logger.info(f"✓ CJ variants fetched for {pid}: {len(data['data'])} variants")
            return {"success": True, "variants": data["data"]}
        else:
            return {
                "success": False,
                "error": data.get("message", "Variants not found"),
            }
    except Exception as e:
        logger.error(f"Error querying CJ variants for {pid}: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Dynamic Pricing Engine
# =============================================================================
def calculate_prices(cj_cost: float) -> dict[str, float]:
    """
    Apply the QuantCAI dynamic pricing formula to a CJ product cost.

    Formula:
        Base Cost   = CJ Cost + $15.00 (covers shipping/handling margin)
        Retail      = Base Cost × 2.0 (100% markup = healthy profit margin)
        Strikethrough = Base Cost × 3.0 (creates perceived value / "sale" anchor)

    Args:
        cj_cost: The raw cost price from CJ Dropshipping

    Returns:
        dict with 'cost', 'retail', and 'strikethrough' prices, all rounded to 2 decimals
    """
    base_cost = cj_cost + 15.0
    retail_price = base_cost * 2.0
    strikethrough_price = base_cost * 3.0

    return {
        "cost": round(cj_cost, 2),
        "retail": round(retail_price, 2),
        "strikethrough": round(strikethrough_price, 2),
    }


# =============================================================================
# Bulk SPU Importer — The Magic Importer
# =============================================================================
async def bulk_import_from_text(raw_text: str) -> list[dict[str, Any]]:
    """
    The Magic Bulk SPU Importer.

    Accepts raw text (pasted SPU codes, CSV data, emails, anything) and uses
    regex to extract CJ SPU/PID codes. Then queries each via the CJ product
    API to fetch full product data including high-res images and videoList.

    The regex pattern matches common CJ identifier formats:
    - CJ followed by alphanumeric chars (e.g., CJ123456789)
    - Pure numeric PIDs of 8+ digits
    - Alphanumeric codes that look like product IDs

    Args:
        raw_text: Raw text containing CJ SPU codes in any format

    Returns:
        List of dicts, each containing 'spu', 'success', and either
        'product' data (with calculated prices) or 'error' message
    """
    # Extract SPU codes using regex — matches CJ-prefixed codes and long numeric IDs
    # Pattern explanation:
    #   CJ[A-Za-z0-9]+   — Matches "CJ" followed by alphanumeric chars
    #   \b\d{8,}\b        — Matches standalone 8+ digit numbers (numeric PIDs)
    spu_codes = re.findall(r"(?:CJ[A-Za-z0-9]+|\b\d{8,}\b)", raw_text)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_spus: list[str] = []
    for code in spu_codes:
        if code not in seen:
            seen.add(code)
            unique_spus.append(code)

    if not unique_spus:
        logger.warning("No SPU codes found in the provided text")
        return []

    logger.info(f"Bulk import: extracted {len(unique_spus)} unique SPU codes")

    results: list[dict[str, Any]] = []

    for spu in unique_spus:
        try:
            # Query CJ for the full product data
            res = await query_cj_product(spu)
            if not res["success"]:
                results.append({"spu": spu, "success": False, "error": res["error"]})
                continue

            product = res["product"]

            # Apply dynamic pricing engine
            cj_cost = float(
                product.get("sellPrice", product.get("productPriceMin", 12.0))
            )
            prices = calculate_prices(cj_cost)

            # Extract media arrays
            product_images: list[str] = []
            if product.get("productImageSet"):
                product_images = [
                    img.get("imageUrl", "") for img in product["productImageSet"]
                    if img.get("imageUrl")
                ]
            elif product.get("productImage"):
                product_images = [product["productImage"]]

            video_list: list[str] = []
            if product.get("videoList"):
                video_list = [
                    v.get("videoUrl", "") for v in product["videoList"]
                    if v.get("videoUrl")
                ]

            # Compose the import-ready product data
            import_data = {
                "spu": spu,
                "success": True,
                "product": {
                    "pid": product.get("pid", spu),
                    "cjSpuCode": spu,
                    "productName": product.get("productName", ""),
                    "productSku": product.get("productSku", f"LV-CJ-{spu}"),
                    "description": product.get("description", ""),
                    "categoryName": product.get("categoryName", "General"),
                    "productImage": product.get("productImage", ""),
                    "productImages": product_images,
                    "productVideo": video_list[0] if video_list else None,
                    "cjVideoList": video_list,
                    "inventory": int(product.get("inventory", 100)),
                    # Dynamic pricing applied
                    "costPrice": prices["cost"],
                    "sellPrice": prices["retail"],
                    "originalPrice": prices["strikethrough"],
                },
            }
            results.append(import_data)
            logger.info(
                f"✓ Bulk import: {spu} → ${prices['cost']} cost → "
                f"${prices['retail']} retail → ${prices['strikethrough']} strikethrough"
            )

        except Exception as e:
            logger.error(f"Bulk import error for SPU {spu}: {e}")
            results.append({"spu": spu, "success": False, "error": str(e)})

    return results


# =============================================================================
# Zero-Touch Fulfillment — CJ Order Creation
# =============================================================================
async def create_cj_order(
    order_id: str,
    shipping_info: dict[str, str],
    line_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Zero-Touch Fulfillment: Create an order on CJ Dropshipping.

    Calls /api2.0/v1/shopping/order/createOrderV2 with payType=2 to enforce
    automated wallet balance deduction. This means CJ will immediately charge
    the wallet and begin processing the order — no manual payment needed.

    IMPORTANT: payType=2 is HARDCODED. This is intentional — it enables
    fully autonomous fulfillment without human intervention. Ensure the
    CJ wallet has sufficient balance before enabling this in production.

    Args:
        order_id: Our internal order ID (for tracking)
        shipping_info: Dict with keys: firstName, lastName, phone, email,
                       address, city, province, zip, country (2-letter ISO)
        line_items: List of dicts, each with: vid (CJ variant ID), quantity

    Returns:
        dict with 'success' bool, 'cj_order_id' string, or 'error' message
    """
    headers = await _get_auth_headers()
    if not headers:
        return {"success": False, "error": "Cannot authenticate with CJ"}

    # Build the CJ order payload
    # CRITICAL: payType=2 = automated wallet deduction (no manual payment)
    payload: dict[str, Any] = {
        "orderNumber": order_id,
        "shippingZip": shipping_info.get("zip", ""),
        "shippingCountry": shipping_info.get("country", "US"),
        "shippingCountryState": shipping_info.get("province", ""),
        "shippingCity": shipping_info.get("city", ""),
        "shippingAddress": shipping_info.get("address", ""),
        "shippingCustomerName": (
            f"{shipping_info.get('firstName', '')} "
            f"{shipping_info.get('lastName', '')}"
        ).strip(),
        "shippingPhone": shipping_info.get("phone", ""),
        "remark": f"QuantCAI Auto-Fulfillment | Internal: {order_id}",
        # ============================================================
        # payType=2: HARDCODED — Wallet balance auto-deduction
        # This is the core of zero-touch fulfillment. CJ will charge
        # the wallet immediately and process the order autonomously.
        # ============================================================
        "payType": 2,
        "products": [
            {
                "vid": item["vid"],
                "quantity": item["quantity"],
            }
            for item in line_items
            if item.get("vid")
        ],
    }

    url = f"{CJ_BASE_URL}/shopping/order/createOrderV2"

    try:
        data = await _cj_post(url, payload, headers)

        if data.get("code") == 200 and data.get("data"):
            cj_order_id = data["data"].get("orderId", "")
            logger.info(
                f"✓ CJ order created: {cj_order_id} | "
                f"Internal: {order_id} | payType=2 (wallet auto-deduction)"
            )
            return {
                "success": True,
                "cj_order_id": cj_order_id,
                "cj_response": data["data"],
            }
        else:
            error_msg = data.get("message", "Order creation failed")
            logger.error(f"CJ order creation failed: {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"CJ order creation error for {order_id}: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Order Tracking — Query CJ order status
# =============================================================================
async def get_cj_order_status(cj_order_id: str) -> dict[str, Any]:
    """
    Query the status of a CJ order by its CJ order ID.

    Args:
        cj_order_id: The CJ-assigned order ID from createOrderV2 response

    Returns:
        dict with 'success' bool and order status data or 'error'
    """
    headers = await _get_auth_headers()
    if not headers:
        return {"success": False, "error": "Cannot authenticate with CJ"}

    url = f"{CJ_BASE_URL}/shopping/order/getOrderDetail?orderId={cj_order_id}"
    try:
        data = await _cj_get(url, headers)
        if data.get("code") == 200 and data.get("data"):
            return {"success": True, "order": data["data"]}
        else:
            return {
                "success": False,
                "error": data.get("message", "Order not found"),
            }
    except Exception as e:
        logger.error(f"Error querying CJ order {cj_order_id}: {e}")
        return {"success": False, "error": str(e)}
