from app.api import chat_context
﻿import os
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
    description="CHUDO AI - Production API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Validation error"}
    )

@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "connected"
    redis_status = "connected"
    
    try:
        await run_in_threadpool(_check_db_sync)
    except Exception as e:
        logger.error(f"Health DB check failed: {e}")
        db_status = "disconnected"
    
    try:
        r = get_redis()
        if r:
            r.ping()
        else:
            redis_status = "not_configured"
    except Exception:
        redis_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "redis": redis_status
    }

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", tags=["Root"])
async def root():
    if os.path.isfile("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.on_event("startup")
async def startup_event():
    import app.models.message
    from app.db.base import Base
    from app.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
app.include_router(chat_context.router, prefix="/api/v1")