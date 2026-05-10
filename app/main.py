"""
RAG Knowledge Base API
Entry point for the FastAPI application.
"""

import logging
import time
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment & Logging
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
APP_NAME = os.getenv("APP_NAME", "RAG Knowledge Base API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ---------------------------------------------------------------------------
# FastAPI Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "A Retrieval-Augmented Generation (RAG) knowledge base API built with FastAPI. "
        "Provides document ingestion, vector search, and AI-powered Q&A endpoints."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# 1. CORS — allow configurable origins (default: all in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Trusted Hosts — guards against HTTP Host header attacks
if ALLOWED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


# 3. Request Logging — logs method, path, status code, and latency
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %s  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Startup / Shutdown Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 %s v%s starting up in [%s] mode", APP_NAME, APP_VERSION, ENVIRONMENT)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 %s shutting down", APP_NAME)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"], summary="API root")
async def root():
    """Returns a welcome message and basic API information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """
    Liveness / readiness probe.

    Returns HTTP 200 with a JSON payload containing service status,
    version, and current environment.  Suitable for use with Docker
    HEALTHCHECK, Kubernetes liveness probes, or any uptime monitor.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": APP_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
        },
    )
