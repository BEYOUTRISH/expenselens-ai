"""
ExpenseLens AI - Main FastAPI Application
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.api import upload, cleaning, analytics, anomalies, insights, forecasting, assistant, export, settings_route

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ExpenseLens AI...")
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
        logger.info("Continuing without SQL database (session-only mode)")
    
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS origins: {settings.get_cors_origins()}")
    yield
    logger.info("Shutting down ExpenseLens AI...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(cleaning.router, prefix="/api", tags=["Cleaning"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(anomalies.router, prefix="/api", tags=["Anomalies"])
app.include_router(insights.router, prefix="/api", tags=["Insights"])
app.include_router(forecasting.router, prefix="/api", tags=["Forecasting"])
app.include_router(assistant.router, prefix="/api", tags=["Assistant"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(settings_route.router, prefix="/api", tags=["Settings"])


@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
async def health():
    db_type = settings.database_url.split("://")[0] if settings.database_url else "sqlite"
    return {
        "status": "ok", 
        "app": settings.app_name, 
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_type
    }
