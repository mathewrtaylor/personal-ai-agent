# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key

async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """
    Get current user from JWT token (optional authentication)
    Returns user info if token is valid, None if no token provided
    """
    if not credentials:
        return {"user_id": "default_user", "authenticated": False}
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload.get("user_id", "default_user"),
        "authenticated": True,
        "token_data": payload
    }

def create_user_session(user_id: str, additional_data: dict = None) -> str:
    """Create a user session token"""
    token_data = {
        "user_id": user_id,
        "session_start": datetime.utcnow().isoformat(),
        "type": "session"
    }
    
    if additional_data:
        token_data.update(additional_data)
    
    return create_access_token(token_data, expires_delta=timedelta(days=30))

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def get_headers() -> dict:
        """Get security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Basic input sanitization"""
    if not text:
        return ""
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def validate_user_id(user_id: str) -> bool:
    """Validate user ID format"""
    if not user_id:
        return False
    
    # Allow alphanumeric, underscores, hyphens, max 50 chars
    import re
    pattern = r'^[a-zA-Z0-9_-]{1,50}$'
    return bool(re.match(pattern, user_id))

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow()
        
        if key not in self._requests:
            self._requests[key] = []
        
        # Clean old requests
        cutoff = now - timedelta(seconds=window_seconds)
        self._requests[key] = [
            req_time for req_time in self._requests[key] 
            if req_time > cutoff
        ]
        
        # Check if under limit
        if len(self._requests[key]) >= max_requests:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 3600):
    """Decorator to check rate limits"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator