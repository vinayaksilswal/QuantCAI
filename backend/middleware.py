import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from security import redis_client
from core.config import settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# RapidAPI Proxy Validation Middleware
# -----------------------------------------------------------------------------
class RapidAPIValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks X-RapidAPI-Proxy-Secret header against a configured secret.
    If the secret header is missing (e.g. stripped on redirects), it checks Redis 
    for a cached active session corresponding to the X-RapidAPI-User header (30s TTL).
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        
        # Exclude paths that do not require proxy validation:
        # - Root/health/docs: public infrastructure endpoints
        # - Auth routes: login/register must work without proxy header
        # - Billing routes: WarriorPlus IPN and PayPal webhooks are server-to-server
        # - Entitlements: queried by frontend with JWT, not proxy
        excluded_prefixes = [
            "/auth/",
            "/api/auth/",
            "/api/billing/",
            "/billing/",
            "/api/payment/",
            "/api/v1/entitlements",
            "/docs",
            "/openapi.json",
            "/health",
            "/healthz",
            "/ready",
        ]
        if path == "/" or any(path.startswith(prefix) for prefix in excluded_prefixes):
            return await call_next(request)

        proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
        expected_secret = settings.RAPIDAPI_PROXY_SECRET
        if not expected_secret:
            return await call_next(request)
        rapidapi_user = request.headers.get("X-RapidAPI-User")

        # 1. Direct secret verification
        if proxy_secret:
            if expected_secret and proxy_secret == expected_secret:
                # Valid secret. Cache the session in Redis if user identity is available
                if rapidapi_user:
                    try:
                        # Cache the validation state for 30 seconds
                        await redis_client.setex(f"rapidapi_session:{rapidapi_user}", 30, "1")
                    except Exception as e:
                        logger.error(f"Failed to cache RapidAPI session in Redis: {e}")
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid X-RapidAPI-Proxy-Secret header value"}
                )

        # 2. Redirect/stripped header fallback (verify via cached Redis session)
        if rapidapi_user:
            try:
                cached_valid = await redis_client.get(f"rapidapi_session:{rapidapi_user}")
                if cached_valid == "1":
                    return await call_next(request)
            except Exception as e:
                logger.error(f"Error querying Redis session cache for RapidAPI validation: {e}")

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-RapidAPI-Proxy-Secret, and no valid session cached in Redis"}
            )

        # 3. Missing validation attributes entirely
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing RapidAPI Proxy verification headers"}
        )

# -----------------------------------------------------------------------------
# Slowapi Rate Limiting Configuration
# -----------------------------------------------------------------------------
def custom_key_func(request: Request) -> str:
    """
    Generate rate-limiting key scoped by identity AND endpoint.
    This prevents a burst of requests on one endpoint from blocking
    access to other endpoints.
    
    Key format: {identity}:{path_prefix}
    - identity: api_key_id > user_id > IP address
    - path_prefix: first 2 path segments (e.g., /api/v1)
    """
    # Determine identity
    if hasattr(request.state, "api_key_id"):
        identity = f"apikey:{request.state.api_key_id}"
    elif hasattr(request.state, "user_id"):
        identity = f"user:{request.state.user_id}"
    else:
        identity = get_remote_address(request)
    
    # Scope by endpoint path prefix (first 2 segments)
    path_parts = request.url.path.strip("/").split("/")[:2]
    path_prefix = "/".join(path_parts) if path_parts else "root"
    
    return f"{identity}:{path_prefix}"

# Limiter object to attach to the FastAPI application
limiter = Limiter(key_func=custom_key_func)

def get_rate_limit(request: Request) -> str:
    """
    Dynamically resolve rate limits based on client subscription tier:
    - free: 20/minute
    - pro: 200/minute
    - enterprise: 2000/minute
    """
    tier = getattr(request.state, "tier", "free")
    if tier == "enterprise":
        return "2000/minute"
    elif tier == "pro":
        return "200/minute"
    else:
        return "20/minute"
