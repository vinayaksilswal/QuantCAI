import logging
import time
import asyncio
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uuid
from fastapi import FastAPI, Depends, HTTPException, Request, status, Response
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

# Sentry configuration (Placeholder for Phase 2 hardening)
# import sentry_sdk
# sentry_sdk.init(
#     dsn="YOUR_SENTRY_DSN",
#     traces_sample_rate=1.0,
#     profiles_sample_rate=1.0,
# )
logger = logging.getLogger("quantcai.main")

from core.logger import get_structlog_logger
struct_logger = get_structlog_logger("quantcai.requests")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that handles startup and shutdown operations.
    """
    logger.info("Initializing QuantCAI FastAPI Backend...")
    
    # Start periodic DB sync task (every 5 minutes)
    from metering_middleware import flush_cumulative_metrics_to_db
    
    async def periodic_metric_flush_loop():
        while True:
            try:
                await asyncio.sleep(300)
                await flush_cumulative_metrics_to_db()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic metric flush loop: {e}")
                
    flush_task = asyncio.create_task(periodic_metric_flush_loop())
    
    yield
    # Shutdown operations
    logger.info("Shutting down QuantCAI FastAPI Backend...")
    app.state.is_shutting_down = True
    
    # Cancel periodic DB sync task
    flush_task.cancel()
    try:
        await flush_task
    except asyncio.CancelledError:
        pass
    
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

# CORS configuration — restrict to specific methods and headers in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization", "Content-Type", "X-API-Key", "X-Requested-With",
        "X-RapidAPI-Proxy-Secret", "X-RapidAPI-User", "X-RapidAPI-Key",
        "Accept", "Origin", "Cache-Control",
    ],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
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
    if settings.is_production or settings.is_staging:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Request size limit middleware — prevents oversized QASM/payload attacks
@app.middleware("http")
async def enforce_request_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "status": "error",
                "error": "REQUEST_TOO_LARGE",
                "message": f"Request body exceeds the maximum allowed size of "
                           f"{settings.MAX_REQUEST_SIZE_BYTES // 1024}KB."
            }
        )
    return await call_next(request)

# Request ID & Logging Middleware
@app.middleware("http")
async def log_requests_and_assign_id(request: Request, call_next):
    if request.url.path in ("/health", "/healthz", "/ready"):
        return await call_next(request)
        
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
        
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Inject request ID into response headers
    response.headers["X-Request-ID"] = request_id
    
    user_id = getattr(request.state, "user_id", None)
    
    struct_logger.info(
        "request_processed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time_ms=round(duration_ms, 2),
        user_id=user_id,
        client_ip=request.client.host if request.client else "unknown"
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
from tier_limits import enforce_limits

from billing import router as billing_router
app.include_router(billing_router)

from routers.payment import router as payment_router
app.include_router(payment_router)

from routers.paypal_billing import router as stripe_billing_router
app.include_router(stripe_billing_router)

from quantum_engine import router as quantum_sim_router
app.include_router(quantum_sim_router, dependencies=[Depends(enforce_limits("simulator"))])

from qasm_engine import router as qasm_sim_router
app.include_router(qasm_sim_router, dependencies=[Depends(enforce_limits("simulator"))])

from routers.pqc import router as pqc_router
app.include_router(pqc_router, dependencies=[Depends(enforce_limits("pqc"))])

from auth import router as developer_keys_router
app.include_router(developer_keys_router)

from routers.developer import router as developer_router
app.include_router(developer_router)

from routers.developer_api import router as developer_api_router
app.include_router(developer_api_router)

from routers.cohorts import router as cohorts_router
app.include_router(cohorts_router)

from routers.ast import router as ast_router
app.include_router(ast_router)

from routers.public_circuit import router as public_circuit_router
app.include_router(public_circuit_router)

from routers.public_badge import router as public_badge_router
app.include_router(public_badge_router)

from routers.auth import router as auth_router
app.include_router(auth_router)

from routers.users import router as users_router
app.include_router(users_router)

from routers.circuit import router as circuit_router, public_router as circuit_public_router
app.include_router(circuit_router, dependencies=[Depends(enforce_limits("circuit"))])
# Mounted WITHOUT enforce_limits: shared-circuit links are opened by anonymous
# visitors, and the router-level dependency above would 401 every one of them.
app.include_router(circuit_public_router)

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

from routers.quantai import router as quantai_router
app.include_router(quantai_router, dependencies=[Depends(enforce_limits("quantai"))])

from routers.entitlements import router as entitlements_router
app.include_router(entitlements_router)

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
async def readiness_check(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Detailed readiness check endpoint.
    Validates database and Redis cache connectivity.
    """
    db_ok = "ok"
    redis_ok = "ok"
    
    if getattr(request.app.state, "is_shutting_down", False):
        return JSONResponse(
            status_code=503,
            content={
                "status": "shutting_down",
                "message": "Server is shutting down",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
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

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    """Dynamic sitemap covering all public-facing routes with lastmod dates."""
    pages = [
        {"loc": "https://quantcai.in/", "changefreq": "daily", "priority": "1.0"},
        {"loc": "https://quantcai.in/learn", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://quantcai.in/pqc-scanner", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://quantcai.in/quantum-simulator", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://quantcai.in/circuit-builder", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://quantcai.in/quantum-states", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://quantcai.in/quantum-computing", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://quantcai.in/enterprise", "changefreq": "monthly", "priority": "0.9"},
        {"loc": "https://quantcai.in/tools", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://quantcai.in/community", "changefreq": "weekly", "priority": "0.6"},
        {"loc": "https://quantcai.in/vision", "changefreq": "monthly", "priority": "0.5"},
        {"loc": "https://quantcai.in/get-started", "changefreq": "monthly", "priority": "0.8"},
        {"loc": "https://quantcai.in/learn/qubits", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://quantcai.in/learn/gates", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://quantcai.in/learn/pqc", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://quantcai.in/terms", "changefreq": "yearly", "priority": "0.3"},
        {"loc": "https://quantcai.in/privacy", "changefreq": "yearly", "priority": "0.3"},
        {"loc": "https://quantcai.in/refund-policy", "changefreq": "yearly", "priority": "0.3"},
        {"loc": "https://quantcai.in/security", "changefreq": "monthly", "priority": "0.5"},
    ]
    
    # 20 Programmatic SEO Landing Pages
    pseo_slugs = [
        "quantum-teleportation", "grovers-algorithm", "bell-state", "quantum-fourier-transform",
        "deutsch-jozsa", "quantum-error-correction", "ghz-state", "quantum-phase-estimation",
        "swap-test", "quantum-key-distribution", "shors-algorithm", "pqc-ml-kem-explainer",
        "pqc-ml-dsa-explainer", "variational-quantum-eigensolver", "quantum-approximate-optimization",
        "quantum-random-number-generator", "bernstein-vazirani", "quantum-walk",
        "harvest-now-decrypt-later", "pqc-tls-handshake"
    ]
    
    for slug in pseo_slugs:
        pages.append({"loc": f"https://quantcai.in/simulate/{slug}", "changefreq": "monthly", "priority": "0.8"})
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    urls_xml = ""
    for page in pages:
        urls_xml += f"""    <url>
        <loc>{page['loc']}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
    </url>
"""
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}</urlset>"""
    return Response(content=xml_content, media_type="application/xml")


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """Serve robots.txt with crawl directives from the API level."""
    content = """User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/
Disallow: /auth/callback
Disallow: /profile

Sitemap: https://quantcai.in/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")
