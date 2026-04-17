import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CHUDO AI"
    APP_VERSION: str = "5.3.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Без дефолтов в production. Если env не задан — падаем при старте.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    # Список CORS-origins ( Railway сам добавит фронтенд-URL )
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # GROQ / Telegram / Stripe
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Убирает async-драйвер для Alembic и sync-коннектов."""
        if not self.DATABASE_URL:
            return ""
        url = self.DATABASE_URL
        # Убираем asyncpg / aiopg
        url = url.replace("+asyncpg", "").replace("+aiopg", "")
        # На всякий случай чистим дублирующий postgresql+
        if url.startswith("postgresql+") and "async" in url:
            url = url.replace("postgresql+asyncpg", "postgresql")
        return url
    
    def get_allowed_origins(self) -> List[str]:
        if "," in self.ALLOWED_ORIGINS:
            return [x.strip() for x in self.ALLOWED_ORIGINS.split(",")]
        return [self.ALLOWED_ORIGINS]

settings = Settings()

# Валидация: если SECRET_KEY пустой в production — падаем сразу
if not settings.DEBUG and not settings.SECRET_KEY:
    raise RuntimeError("FATAL: SECRET_KEY must be set in production environment")
