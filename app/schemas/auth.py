from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserRegister(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    uuid: str
    email: EmailStr
    full_name: Optional[str] = None
    subscription_tier: SubscriptionTier
    daily_requests_remaining: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    @field_validator('uuid', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
