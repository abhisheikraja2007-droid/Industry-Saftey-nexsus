import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import jwt

# Oauth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_jwt_secrets() -> List[str]:
    """
    Get all configured JWT secrets.
    Allows zero-downtime rotation. The first secret is used for signing,
    while all secrets are tried for verification.
    """
    secrets_str = os.getenv("JWT_SECRET", "super-secret-key-change-me-in-production")
    return [s.strip() for s in secrets_str.split(",") if s.strip()]

def get_active_secret() -> str:
    secrets = get_jwt_secrets()
    return secrets[0] if secrets else "super-secret-key-change-me-in-production"

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_active_secret(), algorithm="HS256")

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire, "refresh": True})
    return jwt.encode(to_encode, get_active_secret(), algorithm="HS256")

def decode_token(token: str) -> dict:
    """
    Verify and decode JWT token using list of valid secrets.
    """
    secrets = get_jwt_secrets()
    last_err = None
    for sec in secrets:
        try:
            return jwt.decode(token, sec, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            last_err = e
            continue
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def is_token_blacklisted(token: str) -> bool:
    from database import AsyncSessionLocal
    from models.user import TokenBlacklist
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TokenBlacklist).where(TokenBlacklist.token == token))
        return result.scalar_one_or_none() is not None

async def blacklist_token(token: str) -> None:
    from database import AsyncSessionLocal
    from models.user import TokenBlacklist
    async with AsyncSessionLocal() as session:
        db_black = TokenBlacklist(token=token)
        session.add(db_black)
        await session.commit()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        # Allow default operator for unauthenticated access or raise unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been blacklisted / logged out",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from database import AsyncSessionLocal
    from models.user import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return {
            "username": user.username,
            "role": user.role,
            "id": str(user.id)
        }

def require_role(allowed_roles: List[str]):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient permissions",
            )
        return current_user
    return dependency
