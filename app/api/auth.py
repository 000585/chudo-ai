from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid

from app.db.base import get_db
from app.models.user import User, SubscriptionTier
from app.models.token import RefreshToken
from app.schemas import UserRegister, UserResponse, Token, TokenRefresh
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    
    user_uuid = payload.get("sub")
    if user_uuid is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        subscription_tier=SubscriptionTier.FREE,
        daily_requests_remaining=20,
        is_active=True,
        is_verified=False,
        uuid=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(subject=str(user.uuid))
    refresh_token = create_refresh_token(subject=str(user.uuid))
    
    refresh = RefreshToken(
        token=refresh_token,
        user_uuid=user.uuid,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(refresh)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    stored = db.query(RefreshToken).filter(
        RefreshToken.token == token_data.refresh_token,
        RefreshToken.is_revoked == 0,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or expired"
        )
    
    user_uuid = payload.get("sub")
    user = db.query(User).filter(User.uuid == user_uuid).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    new_access = create_access_token(subject=user_uuid)
    new_refresh = create_refresh_token(subject=user_uuid)
    
    stored.is_revoked = 1
    
    refresh = RefreshToken(
        token=new_refresh,
        user_uuid=user.uuid,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(refresh)
    db.commit()
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 1800
    }

@router.post("/logout")
async def logout(
    token_data: TokenRefresh,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stored = db.query(RefreshToken).filter(
        RefreshToken.token == token_data.refresh_token,
        RefreshToken.user_uuid == current_user.uuid
    ).first()
    
    if stored:
        stored.is_revoked = 1
        db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
