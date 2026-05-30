import logging
import time
import asyncio
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import database configuration and pool from core
from core.database import engine, get_db
from core.config import settings
from middleware import RapidAPIValidationMiddleware, limiter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("quantcai.main")

# Configure structlog for request logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
struct_logger = structlog.get_logger("quantcai.requests")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that handles startup and shutdown operations.
    """
    logger.info("Initializing QuantCAI FastAPI Backend...")
    yield
    # Shutdown operations
    logger.info("Shutting down QuantCAI FastAPI Backend...")
    
    # 1. Wait for active Celery tasks to complete (max 30s)
    try:
        from worker import celery_app
        inspector = celery_app.control.inspect()
        start_time = time.time()
        while time.time() - start_time < 30:
            active = inspector.active()
            if not active or not any(tasks for tasks in active.values()):
                logger.info("No active Celery tasks remaining.")
                break
            logger.info("Waiting for active Celery tasks to complete...")
            await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"Error checking active Celery tasks on shutdown: {e}")

    # 2. Close Redis connection pool
    try:
        from security import redis_client
        logger.info("Closing Redis connection pool...")
        await redis_client.close()
        logger.info("Redis connection pool closed.")
    except Exception as e:
        logger.warning(f"Error closing Redis client: {e}")

    # 3. Dispose connection pool
    logger.info("Disposing connection pool...")
    await engine.dispose()
    logger.info("Connection pool disposed successfully.")

app = FastAPI(
    title="QuantCAI API",
    description="Backend API for QuantCAI SaaS platform featuring subscriptions, metering, and enterprise contracts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount RapidAPI middleware
app.add_middleware(RapidAPIValidationMiddleware)

# Mount SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path in ("/health", "/healthz", "/ready"):
        return await call_next(request)
        
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    user_id = getattr(request.state, "user_id", None)
    
    struct_logger.info(
        "request_processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time_ms=round(duration_ms, 2),
        user_id=user_id
    )
    return response

# Standardized Validation Error Exception Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if hasattr(status, "HTTP_422_UNPROCESSABLE_ENTITY") else 422,
        content={
            "status": "error",
            "message": "Validation failed",
            "detail": exc.errors(),
            "details": exc.errors()
        }
    )

# Standardized HTTP Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    headers = exc.headers if hasattr(exc, "headers") else None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "detail": exc.detail,
            "details": None
        },
        headers=headers
    )

# Standardized Global Catch-All Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred on {request.url.path}: {str(exc)}", exc_info=exc)
    message = "Internal server error" if settings.is_production else str(exc)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": message,
            "detail": message,
            "details": None
        }
    )

# Include API routers
from billing import router as billing_router
app.include_router(billing_router)

from quantum_engine import router as quantum_sim_router
app.include_router(quantum_sim_router)

from routers.pqc import router as pqc_router
app.include_router(pqc_router)

from auth import router as developer_keys_router
app.include_router(developer_keys_router)

from routers.auth import router as auth_router
app.include_router(auth_router)

from routers.users import router as users_router
app.include_router(users_router)

from routers.circuit import router as circuit_router
app.include_router(circuit_router)

from routers.content import router as content_router
app.include_router(content_router)

from routers.chat import router as chat_router
app.include_router(chat_router)

from routers.community import router as community_router
app.include_router(community_router)

from routers.admin import router as admin_router
app.include_router(admin_router)

from tutor import router as tutor_router
app.include_router(tutor_router)

@app.get("/healthz")
def liveness_check():
    """
    Fast liveness check endpoint.
    Returns 200 OK immediately if the web process is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "QuantCAI API"
    }

@app.get("/ready")
@app.get("/health")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed readiness check endpoint.
    Validates database and Redis cache connectivity.
    """
    db_ok = "ok"
    redis_ok = "ok"
    
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_ok = "error"
        
    # Check Redis
    try:
        from security import redis_client
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_ok = "error"
        
    status = "healthy"
    status_code = 200
    if db_ok == "error" or redis_ok == "error":
        status = "degraded"
        status_code = 503
        
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "database": db_ok,
            "redis": redis_ok,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.get("/")
def read_root():
    """Root endpoint returning basic application metadata."""
    return {
        "name": "QuantCAI API",
        "description": "Multi-tenant SaaS & API Platform Backend",
        "status": "online"
    }
