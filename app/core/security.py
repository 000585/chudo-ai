from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from typing import Optional
import hashlib

# Фикс для bcrypt — используем SHA256 перед хешированием чтобы обойти 72 bytes limit
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def normalize_password(password: str) -> str:
    """Нормализация пароля через SHA256 чтобы снять ограничение bcrypt в 72 байта"""
    if isinstance(password, str):
        return hashlib.sha256(password.encode()).hexdigest()
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля с нормализацией"""
    normalized = normalize_password(plain_password)
    return pwd_context.verify(normalized, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширование пароля с нормализацией"""
    normalized = normalize_password(password)
    return pwd_context.hash(normalized)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": subject, "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": subject, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
