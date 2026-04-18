from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" или "assistant"
    content = Column(Text, nullable=False)
    model = Column(String(50), nullable=True)  # какая модель отвечала
    created_at = Column(DateTime(timezone=True), server_default=func.now())