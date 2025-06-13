from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token
)
from app.core.config import settings
from app.auth.models import User
from app.auth.schemas import (
    UserCreate,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserInDB,
    UserRole,
    UserLogin,
    UserLoginWithRole
)
from app.utils.email import send_reset_password_email
from app.exception import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError
)
from app.core.dependencies import (
    get_current_user,
    require_admin,
    require_user
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserInDB)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with same email AND role already exists
    existing_user = db.query(User).filter(
        User.email == user.email,
        User.role == user.role
    ).first()

    if existing_user:
        raise EmailAlreadyRegisteredError()

    # Remove admin creation restriction
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/signin", response_model=Token)
async def login(
        request: Request,
        user_login: UserLoginWithRole,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == user_login.email,User.role==user_login.role).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Verify the requested role matches the user's actual role
    if user.role != user_login.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have {user_login.role} privileges"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(
        request: PasswordResetRequest,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    send_reset_password_email(user.email, reset_token)
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
        request: PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.reset_token == request.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()

    if not user:
        raise InvalidTokenError()

    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password updated successfully"}

# Example of protected routes
