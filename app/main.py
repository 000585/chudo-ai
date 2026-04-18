import os
import time
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api import chat_context
from app.db.base import engine, Base
from app.core.config import settings
from app.core.guardrails import get_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("chudo_ai")

def _check_db_sync():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [env={'dev' if settings.DEBUG else 'prod'}]")

    try:
        await run_in_threadpool(_check_db_sync)
        logger.info("Database connection verified")
        try:
            from app.db.base import Base
            from sqlalchemy.ext.asyncio import create_async_engine
            db_url = settings.DATABASE_URL
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            tmp_engine = create_async_engine(db_url, pool_pre_ping=True)
            async with tmp_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables verified")
        except Exception as e:
            logger.error(f"Table creation check: {e}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError("Cannot start without database") from e

    try:
        r = get_redis()
        if r:
            r.ping()
            logger.info("Redis connection verified")
        else:
            logger.warning("Redis not configured")
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CHUDO AI API with context memory",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(chat_context.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": "Welcome to CHUDO AI", "docs": "/docs"}