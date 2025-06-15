from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
import logging

from app.core.config import settings
from app.core.database import get_db
from app.auth.models import User
from app.auth.schemas import UserRole
from app.core.security import decode_token
from app.exception import InactiveUserError
from fastapi.security import APIKeyHeader
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bearer_scheme = APIKeyHeader(name="Authorization", scheme_name="Bearer")

async def get_current_user(
        token: str = Depends(bearer_scheme),
        db: Session = Depends(get_db)
) -> User:
    # Remove the "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        # Extract all necessary claims
        email: str = payload.get("sub")
        role_str: str = payload.get("role")
        user_id: int = payload.get("id")

        if None in (email, role_str, user_id):
            logger.error("Missing required claims in token")
            raise credentials_exception

        # Convert role string to enum
        try:
            role = UserRole(role_str)
        except ValueError:
            logger.error(f"Invalid role in token: {role_str}")
            raise credentials_exception

    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception

    # Get user by ID
    user = db.query(User).filter(User.id == user_id).first()

    # Additional verification
    if not user:
        logger.error(f"User not found for ID: {user_id}")
        raise credentials_exception
    if user.email != email:
        logger.error(f"Email mismatch: token email {email}, user email {user.email}")
        raise credentials_exception
    if user.role != role:
        logger.error(f"Role mismatch: token role {role}, user role {user.role}")
        raise credentials_exception

    return user

async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Verify the user is active"""
    if not current_user.is_active:
        logger.error(f"User {current_user.email} is inactive")
        raise InactiveUserError()
    return current_user

async def require_admin(
        current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def require_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required"
        )
    return current_user










