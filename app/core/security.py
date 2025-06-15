from datetime import datetime, timedelta
from typing import Optional
import logging
import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    try:
        return pwd_context.hash(password)
    except (ValueError, TypeError) as e:
        logger.error(f"Password hashing error: {str(e)}")
        try:
            # Fallback to direct bcrypt
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            return hashed.decode('utf-8')
        except Exception as bcrypt_e:
            logger.error(f"BCrypt fallback failed: {str(bcrypt_e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error hashing password"
            )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire,"sub": to_encode.get("sub", ""),
                          "role": to_encode.get("role", ""),
                          "id": to_encode.get("id", 0)})

        if not all([to_encode.get("sub"), to_encode.get("role"), to_encode.get("id")]):
            raise ValueError("Missing required token claims")

        token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        logger.info(f"Created token for user: {data.get('sub')} with role: {data.get('role')}")
        return token

    except JWTError as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating token"
        )

# In security.py
def decode_token(token: str) -> dict:
    try:
        logger.info(f"Decoding token: {token[:20]}...")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        logger.info(f"Token decoded successfully")
        return {
            "sub": payload.get("sub"),
            "role": payload.get("role")
        }
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected decode error: {str(e)}")
        return None