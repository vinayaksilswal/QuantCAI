import os
import time
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from logger_config import setup_logging
from routers import auth, chat, circuit, community, users

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

# Security Check: Ensure critical API keys are set
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith("your_") or "AIzaSy" not in GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY is missing or appears to be a placeholder. AI features will fail!")

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
    # Strict defaults for production
    allowed_origins = ["http://localhost:5173","https://quantcai.in","http://quantcai.in"] 

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

        # Hardened Security Headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none';")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Request-ID", request_id)

        # Optimization: Filter repetitive logs
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
    except Exception as e:
        logger.error(
            f"Unhandled Error: {request.method} {request.url.path} - {str(e)}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        return await _rate_limit_exceeded_handler(request, e) if isinstance(e, RateLimitExceeded) else \
               HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "QuantCAI API is running"}

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(circuit.router)
app.include_router(community.router)
app.include_router(users.router)
