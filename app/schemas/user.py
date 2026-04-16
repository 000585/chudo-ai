from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserRegister(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})
    
    id: int
    uuid: UUID  # Меняем на тип UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    subscription_tier: str = "free"
    daily_requests_remaining: int = 20
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
