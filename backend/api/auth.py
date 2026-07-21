import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from database import AsyncSessionLocal
from models.user import User
from sqlalchemy import select
from utils.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, blacklist_token, get_current_user, require_role
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "operator" # operator, supervisor, admin

class PasswordResetRequest(BaseModel):
    username: str
    new_password: str

@router.post("/register")
async def register(data: RegisterRequest, current_user: dict = Depends(require_role(["admin"]))):
    async with AsyncSessionLocal() as session:
        # Check if username exists
        existing = await session.execute(select(User).where(User.username == data.username))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        hashed = hash_password(data.password)
        db_user = User(
            username=data.username,
            hashed_password=hashed,
            role=data.role
        )
        session.add(db_user)
        await session.commit()
        return {"status": "user registered", "username": data.username}

@router.post("/login")
async def login(data: LoginRequest):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check lockout
        now = datetime.now(timezone.utc)
        if user.locked_until:
            # SQLAlchemy DateTime timezone comparison
            locked_until_tz = user.locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until_tz:
                time_left = int((locked_until_tz - now).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is locked due to multiple failed logins. Try again in {time_left}s."
                )
            else:
                user.locked_until = None
                user.failed_login_attempts = 0
                await session.commit()

        if not verify_password(data.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked due to multiple failed logins. Try again in 15 minutes."
                )
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Success reset failure count
        user.failed_login_attempts = 0
        user.locked_until = None
        await session.commit()
        
        access_token = create_access_token(data={"sub": user.username, "role": user.role})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role,
            "username": user.username
        }

@router.post("/refresh")
async def refresh(refresh_token: str = Header(...)):
    try:
        payload = decode_token(refresh_token)
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token type"
            )
        
        username = payload.get("sub")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            new_access = create_access_token(data={"sub": user.username, "role": user.role})
            return {"access_token": new_access, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization header required"
        )
    token = authorization.split(" ")[1]
    await blacklist_token(token)
    return {"status": "logged out"}

@router.post("/reset-password")
async def reset_password(data: PasswordResetRequest, current_user: dict = Depends(require_role(["admin"]))):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user.hashed_password = hash_password(data.new_password)
        await session.commit()
        return {"status": "password reset successfully"}

@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
