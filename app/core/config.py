from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CHUDO AI"
    APP_VERSION: str = "5.3.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "postgresql://chudo:chudo_secure_password_2024@db:5432/chudo_db"
    REDIS_URL: str = "redis://:redis_password_2024@redis:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
