import os
import time
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from logger_config import setup_logging
from routers import auth, chat, circuit, community, users

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

# Security Check: Ensure critical API keys are set with proper strength
def validate_secret_key(secret: str) -> bool:
    """Validate that secret key is sufficiently strong."""
    if not secret:
        return False
    # Must be at least 32 bytes (64 hex chars or 32+ random chars)
    if len(secret) < 32:
        return False
    # Reject common placeholder values
    weak_keys = ["change-me", "your_secret_key_here", "secret", "password", "default", "CHANGE_ME"]
    if secret.lower() in weak_keys or "your_" in secret.lower():
        return False
    return True

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith("your_") or "AIzaSy" not in GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY is missing or appears to be a placeholder. AI features will fail!")

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
if not validate_secret_key(AUTH_SECRET_KEY):
    error_msg = "CRITICAL: AUTH_SECRET_KEY is missing, too short, or using a weak default value. Application will not start."
    logger.error(error_msg)
    raise RuntimeError(error_msg)

# Determine environment (default to production)
ENV = os.getenv("ENV", "production").lower()
is_production = ENV == "production"

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="QuantCAI API",
    description="Quantum Computing AI Learning Platform Backend",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Improved CORS Configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    # Strict defaults
    if is_production:
        # Production: Only HTTPS domains
        allowed_origins = [
            "https://quantcai.in",
            "https://www.quantcai.in",
            "https://quantcai.onrender.com"
        ]
    else:
        # Development: Localhost with HTTP allowed
        allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    """Middleware to add request ID, security headers, and log requests/responses."""
    start_time = time.time()
    request_id = str(os.urandom(16).hex())
    client_ip = request.client.host if request.client else "unknown"

    # Skip logging for OPTIONS preflight and Swagger static files
    if request.method == "OPTIONS" or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        return await call_next(request)

    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_method": request.method,
            "request_path": str(request.url.path),
            "request_ip": client_ip,
            "request_id": request_id,
        },
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Security Headers (hardened)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # X-XSS-Protection is deprecated in modern browsers, but keep for legacy
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        # Content Security Policy
        if is_production:
            # Production: Strict CSP, no unsafe-inline, disable Swagger UI
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "frame-ancestors 'none';"
            )
        else:
            # Development: Relaxed CSP to allow Swagger UI CDNs
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https://cdn.jsdelivr.net; "
                "frame-ancestors 'none';"
            )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Request-ID"] = request_id

        # Don't expose too much in logs for OPTIONS
        should_log = True
        if request.method == "OPTIONS":
            should_log = False
        elif request.url.path.endswith("/api/auth/me") and response.status_code == 401:
            should_log = False

        if should_log:
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
                extra={
                    "request_method": request.method,
                    "request_path": str(request.url.path),
                    "response_status": response.status_code,
                    "process_time": process_time,
                    "request_id": request_id,
                },
            )

        return response
    except RateLimitExceeded:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    except Exception as e:
        logger.error(
            f"Unhandled Error: {request.method} {request.url.path} - {str(e)}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )

if is_production:
    # Disable Swagger UI in production via docs_url=None
    app.docs_url = None
    app.redoc_url = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "QuantCAI API is running"}

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(circuit.router)
app.include_router(community.router)
app.include_router(users.router)
