"""
=============================================================================
QuantCAI — FastAPI Application Entry Point
=============================================================================
This is the control center for the entire autonomous e-commerce platform.
It hosts the admin UI, AI chatbot, marketing automation scheduler, and all
API endpoints for CJ Dropshipping, Meta Graph, and Resend integrations.

CRITICAL ARCHITECTURE DECISION:
  The Prisma client is instantiated and connected INSIDE the async lifespan
  context manager — NOT at module level. This ensures the client is bound
  to the active Uvicorn event loop, preventing asyncio.locks.Event errors
  that occur when Prisma is created before the loop starts.

Run locally:
  cd python_admin
  uvicorn main:app --reload --port 8000
=============================================================================
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from prisma import Prisma
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings

# =============================================================================
# Loguru Configuration
# =============================================================================
# Remove default stderr handler and configure based on environment.
# Production: JSON-serialized structured logs for log aggregation.
# Development: Human-readable colored output for debugging.
# =============================================================================
logger.remove()
if settings.environment == "production":
    logger.add(
        sys.stdout,
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        serialize=True,  # JSON output for production log aggregators
    )
else:
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


# =============================================================================
# Application Lifespan — Async Context Manager
# =============================================================================
# This is the ONLY place where Prisma is instantiated and connected.
# The scheduler is also initialized here. Both are torn down on shutdown.
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of critical application resources:
    1. Prisma ORM client (PostgreSQL connection)
    2. APScheduler (bi-hourly marketing automation loop)

    CRUCIAL: Prisma MUST be instantiated inside this async context to bind
    to the active Uvicorn event loop. Creating it at module level causes
    asyncio.locks.Event errors because the event loop doesn't exist yet
    at import time.
    """
    # --- Import scheduler here to avoid circular imports ---
    from services.scheduler import create_scheduler, shutdown_scheduler

    logger.info("=" * 60)
    logger.info("QuantCAI Autonomous E-Commerce Platform — Starting Up")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)

    # --- Step 1: Instantiate and connect Prisma INSIDE the lifespan ---
    # This is the critical fix: creating Prisma() here ensures it uses
    # the current running event loop, not a stale or non-existent one.
    import subprocess
    import sys
    import os
    import glob
    import shutil
    logger.info("Ensuring Prisma engine is available at runtime...")
    try:
        os.environ["PRISMA_CLIENT_ENGINE_TYPE"] = "binary"
        os.environ["PRISMA_CLI_QUERY_ENGINE_TYPE"] = "binary"
        
        existing_engines = glob.glob("prisma-query-engine-*")
        if existing_engines:
            logger.info(f"Prisma engine already exists locally: {existing_engines[0]}, skipping fetch.")
        else:
            logger.warning("Prisma engine not found locally! Fetching at runtime (this may cause Gunicorn timeout in production).")
            subprocess.run([sys.executable, "-m", "prisma", "py", "fetch"], check=True)
            
            # Prisma Python bug: The engine is downloaded to node_modules/@prisma/engines/
            # but the python client looks for it in the current directory or node_modules/prisma/
            cache_dir = "/opt/render/.cache/prisma-python/binaries/*/*/"
            engines = glob.glob(cache_dir + "node_modules/@prisma/engines/query-engine-*")
            
            # If not on Render, try local user cache (for local development)
            if not engines:
                import platform
                home = os.path.expanduser("~")
                cache_dir = os.path.join(home, ".cache", "prisma-python", "binaries", "*", "*", "")
                engines = glob.glob(cache_dir + "node_modules/@prisma/engines/query-engine-*")
                
            if engines:
                engine_path = engines[0]
                # Copy to python_admin current directory with the "prisma-" prefix it expects
                expected_name = "prisma-" + os.path.basename(engine_path)
                shutil.copy(engine_path, expected_name)
                os.chmod(expected_name, 0o755)
                logger.info(f"Fixed Prisma path bug: Copied {engine_path} to {expected_name}")
            else:
                logger.warning("Could not find downloaded Prisma engine in cache directory.")
    except Exception as e:
        logger.error(f"Failed to fetch/setup Prisma engine: {e}")

    prisma_client = Prisma()
    os.environ["DATABASE_URL"] = settings.database_url
    await prisma_client.connect()
    app.state.prisma = prisma_client
    logger.info("Prisma ORM connected to PostgreSQL")

    # --- Step 2: Initialize and start the marketing scheduler ---
    # The scheduler receives the prisma client so it doesn't create its own.
    scheduler = create_scheduler(prisma_client)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("APScheduler started (bi-hourly marketing loop active)")

    logger.info("=" * 60)
    logger.info("QuantCAI is ready to serve requests")
    logger.info("=" * 60)

    yield  # --- Application is running ---

    # --- Shutdown: Clean up resources in reverse order ---
    logger.info("Shutting down QuantCAI...")

    shutdown_scheduler(scheduler)
    logger.info("Scheduler stopped")

    if prisma_client.is_connected():
        await prisma_client.disconnect()
    logger.info("Prisma ORM disconnected")

    logger.info("QuantCAI shutdown complete.")


# =============================================================================
# FastAPI Application Instance
# =============================================================================
app = FastAPI(
    title="QuantCAI Admin & Automation",
    description="AI-Powered Autonomous E-Commerce Platform with Marketing Automation",
    version="2.0.0",
    lifespan=lifespan,
)

# --- Prometheus metrics endpoint at /metrics ---
Instrumentator().instrument(app).expose(app)


# =============================================================================
# Middleware Stack
# =============================================================================
# Order matters: GZip → TrustedHost → CORS
# =============================================================================
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Global Exception Handlers
# =============================================================================
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse | RedirectResponse:
    """
    Custom HTTP exception handler:
    - If a 401 hits an /admin page (not /admin/login), redirect to login.
    - Otherwise, return a structured JSON error response.
    """
    if (
        exc.status_code == 401
        and (request.url.path.startswith("/admin") or request.url.path.startswith("/marketing"))
        and not request.url.path.startswith("/admin/login")
    ):
        return RedirectResponse(url="/admin/login", status_code=303)

    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


import uuid

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler to prevent 500 errors from leaking stack traces."""
    error_id = str(uuid.uuid4())
    logger.exception(f"Unhandled Exception on {request.method} {request.url.path} (Error ID: {error_id})")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error", "error_id": error_id},
    )


# =============================================================================
# Health Check Endpoint
# =============================================================================
@app.get("/logo.png", tags=["System"])
async def serve_logo() -> FileResponse:
    """Serve the application logo."""
    return FileResponse("templates/logo.png")

@app.get("/health", response_model=None)
async def health_check(request: Request) -> dict | JSONResponse:
    """
    Health check endpoint for Render's health monitoring.
    Verifies database connectivity with a simple query.
    """
    try:
        prisma: Prisma = request.app.state.prisma
        await prisma.query_raw("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )


# =============================================================================
# Static Files & Templates
# =============================================================================
# Mount the templates directory for serving CSS/JS assets and the uploads
# directory for manually uploaded media files.
# =============================================================================
app.mount("/static", StaticFiles(directory="templates"), name="static")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


# =============================================================================
# Router Registration
# =============================================================================
# Import and include all routers. The ai_chat router has been consolidated
# into the chat_agent service + the api router.
# =============================================================================
from routers import admin, api, auth, marketing  # noqa: E402

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(marketing.router)
app.include_router(api.router)
app.include_router(api.public_router)


# =============================================================================
# Root Redirect
# =============================================================================
@app.get("/")
async def root() -> RedirectResponse:
    """Redirect the root URL to the admin dashboard."""
    return RedirectResponse(url="/admin", status_code=303)


# =============================================================================
# Quick Stats API (used by the dashboard)
# =============================================================================
@app.get("/api/stats")
async def get_stats(request: Request) -> dict:
    """Return high-level platform statistics for the admin dashboard."""
    prisma: Prisma = request.app.state.prisma
    audience_count = await prisma.audience.count()

    return {
        "success": True,
        "data": {
            "users": 0,
            "orders": 0,
            "audience": audience_count,
            "products": 0,
        },
    }
