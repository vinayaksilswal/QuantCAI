import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from logger_config import setup_logging
from routers import auth, chat, circuit, community, users

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to add a request ID, security headers, and log all requests/responses."""
    start_time = time.time()

    request_id = str(os.urandom(16).hex())
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_method": request.method,
            "request_path": str(request.url.path),
            "request_ip": client_ip,
            "query_params": str(request.query_params) if request.query_params else None,
            "request_id": request_id,
        },
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Request-ID", request_id)

        # Filter out noisy logs:
        # 1. Successful OPTIONS requests (CORS preflight)
        # 2. auth/me 401s (polling when not logged in)
        should_log = True
        if request.method == "OPTIONS" and response.status_code == 200:
            should_log = False
        elif request.url.path.endswith("/api/auth/me") and response.status_code == 401:
            should_log = False

        if should_log:
            logger.info(
                f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s",
                extra={
                    "request_method": request.method,
                    "request_path": str(request.url.path),
                    "request_ip": client_ip,
                    "response_status": response.status_code,
                    "process_time": process_time,
                    "request_id": request_id,
                },
            )

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error processing request: {request.method} {request.url.path} - {str(e)}",
            exc_info=True,
            extra={
                "request_method": request.method,
                "request_path": str(request.url.path),
                "request_ip": client_ip,
                "response_status": 500,
                "process_time": process_time,
                "request_id": request_id,
            },
        )
        raise

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello, World!"}

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(circuit.router)
app.include_router(community.router)
app.include_router(users.router)
