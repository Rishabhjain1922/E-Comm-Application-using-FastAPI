from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.auth.models import User
from app.core.security import decode_token
from app.exception import InactiveUserError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/signin")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    Returns User model instance
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email = payload.get("email")
        if email is None:
            raise credentials_exception

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception

async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Verify the user is active"""
    if not current_user.is_active:
        raise InactiveUserError()
    return current_user

async def get_current_admin(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify the user is an admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_current_customer(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify the user is a regular user"""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required"
        )
    return current_user

# Aliases for clearer usage
require_admin = get_current_admin
require_user = get_current_customer