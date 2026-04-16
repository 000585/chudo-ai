from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
import time

from app.api.auth import router as auth_router
from app.db.base import engine, Base
from app.core.config import settings
from app.core.guardrails import get_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f'?? Starting {settings.APP_NAME} v{settings.APP_VERSION}')
    
    Base.metadata.create_all(bind=engine)
    print('? Database tables verified')
    
    try:
        r = get_redis()
        r.ping()
        print('? Redis connection verified')
    except Exception as e:
        print(f'?? Redis connection failed: {e}')
    
    yield
    
    print(f'?? Shutting down {settings.APP_NAME}')

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description='CHUDO AI - Production API',
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=['*']
)

@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers['X-Process-Time'] = str(process_time)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': exc.errors(), 'message': 'Validation error'}
    )

@app.get('/health', tags=['Health'])
async def health_check():
    from sqlalchemy import text
    
    db_status = 'connected'
    redis_status = 'connected'
    
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
    except Exception:
        db_status = 'disconnected'
    
    try:
        r = get_redis()
        r.ping()
    except Exception:
        redis_status = 'disconnected'
    
    return {
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'version': settings.APP_VERSION,
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'redis': redis_status
    }

app.include_router(auth_router, prefix='/api/v1')

@app.get('/', tags=['Root'])
async def root():
    return {
        'name': settings.APP_NAME,
        'version': settings.APP_VERSION,
        'docs': '/docs',
        'health': '/health'
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'app.main:app',
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
