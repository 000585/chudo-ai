from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import NullPool
from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=300
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session