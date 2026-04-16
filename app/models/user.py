import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.base import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    daily_requests_remaining = Column(Integer, default=20)
    last_request_reset = Column(DateTime, default=datetime.utcnow)
    
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<User(email={self.email}, tier={self.subscription_tier})>"
