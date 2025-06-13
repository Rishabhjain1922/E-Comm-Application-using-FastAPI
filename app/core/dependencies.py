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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

def get_user_by_email(db: Session, email: str) -> Optional[User]:  # Change return type
    return db.query(User).filter(User.email == email).first()


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
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
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
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

async def get_current_admin(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify the user is an admin"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_current_customer(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Verify the user is a regular user"""
    if current_user.role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required"
        )
    return current_user


def get_last_logged_in_user(db: Session = Depends(get_db)):
    # Find the user with the most recent last_login value
    last_user = db.query(User).order_by(User.last_login.desc()).first()

    if not last_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )

    # Create a simple object with user data
    class LastUser:
        def __init__(self, user):
            self.id = user.id
            self.email = user.email
            self.name = user.name
            self.role = user.role
            self.last_login = user.last_login

    return LastUser(last_user)

def verify_admin(user = Depends(get_last_logged_in_user)):
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

def verify_user(user = Depends(get_last_logged_in_user)):
    if user.role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required"
        )
    return user
# Aliases for clearer usage
require_admin = get_current_admin
require_user = get_current_customer
