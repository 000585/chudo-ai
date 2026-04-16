import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    daily_requests_remaining = Column(Integer, default=20)
    
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_jti = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None