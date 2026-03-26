from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# JWT Bearer scheme for Swagger UI
security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def create_access_token(user_id: str, email: str, username: str, role: str) -> str:
    """
    Create a JWT access token with user info and role embedded.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "username": username,
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def create_reset_token(email: str) -> str:
    """
    Create a short-lived JWT token specifically for password resets (15 mins).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {
        "email": email,
        "purpose": "password_reset",
        "exp": expire
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_reset_token(token: str) -> Optional[str]:
    """
    Decode a reset token and return the email if valid.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("email")
    except JWTError as e:
        logger.warning(f"Reset token decode failed: {e}")
        return None

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token. Returns the payload dict or None.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency that extracts and validates the JWT from the Authorization header.
    Returns a dict with user_id, email, username.
    """

    token = credentials.credentials
    payload = decode_access_token(token)

    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "username": payload.get("username"),
        "role": payload.get("role", "student")
    }

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency that ensures the current user has the 'admin' role.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
