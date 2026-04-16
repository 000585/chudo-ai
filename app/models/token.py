from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(512), unique=True, index=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
