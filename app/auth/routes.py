import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets

from app.auth.models import User
from app.auth.schemas import PasswordResetConfirm, PasswordResetRequest, UserLoginWithRole, Token, UserCreate, UserInDB
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.exception import EmailSendError, InvalidCredentialsError, EmailAlreadyRegisteredError, InvalidTokenError
from app.utils.email import send_reset_password_email

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="", tags=["auth"])

@router.post("/signup", response_model=UserInDB)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Signup attempt for email: {user.email} with role: {user.role}")

        # Check if user exists
        existing_user = db.query(User).filter(
            User.email == user.email,
            User.role == user.role
        ).first()

        if existing_user:
            logger.warning(f"Email already registered: {user.email} for role {user.role}")
            raise EmailAlreadyRegisteredError()

        # Create new user
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

        logger.info(f"New user created: {db_user.id} - {db_user.email} ({db_user.role})")
        return db_user

    except Exception as e:
        logger.error(f"Signup failed for {user.email}: {str(e)}")
        raise

@router.post("/signin", response_model=Token)
async def login(
        request: Request,
        user_login: UserLoginWithRole,
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Login attempt for: {user_login.email} as {user_login.role}")

        user = db.query(User).filter(
            User.email == user_login.email,
            User.role == user_login.role
        ).first()

        if not user:
            logger.warning(f"User not found: {user_login.email} with role {user_login.role}")
            raise InvalidCredentialsError()

        if not verify_password(user_login.password, user.hashed_password):
            logger.warning(f"Invalid password for: {user_login.email}")
            raise InvalidCredentialsError()

        if user.role != user_login.role:
            logger.warning(f"Role mismatch for {user_login.email}: requested {user_login.role}, actual {user.role}")
            raise InvalidCredentialsError()

        user.last_login = datetime.utcnow()
        db.commit()

        access_token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role.value,
                "id": user.id
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"Login successful for: {user_login.email}")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Login failed for {user_login.email}: {str(e)}")
        raise

@router.post("/forgot-password")
async def forgot_password(
        request: PasswordResetRequest,
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Password reset requested for: {request.email} ({request.role})")

        user = db.query(User).filter(
            User.email == request.email,
            User.role == request.role
        ).first()

        if not user:
            logger.info(f"No user found for reset: {request.email} ({request.role})")
            return {"message": "If the email exists for this role, a reset link has been sent"}


        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
        db.commit()

        logger.info(f"Reset token generated for: {request.email} ({request.role})")

        try:
            send_reset_password_email(user.email, reset_token, request.role)
            logger.info(f"Password reset email sent to: {request.email}")
        except Exception as e:
            logger.error(f"Failed to send reset email to {request.email}: {str(e)}")
            raise EmailSendError("Failed to send reset email")

        return {"message": "If the email exists, a reset link has been sent"}

    except Exception as e:
        logger.error(f"Password reset failed for {request.email}: {str(e)}")
        raise

@router.post("/reset-password")
async def reset_password(
        request: PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Password reset attempt with token: {request.token[:6]}...")

        user = db.query(User).filter(
            User.reset_token == request.token,
            User.reset_token_expires > datetime.utcnow(),
            User.role == request.role
        ).first()

        if not user:
            logger.warning(f"Invalid reset token: {request.token[:6]}...")
            raise InvalidTokenError()

        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        logger.info(f"Password reset successful for: {user.email}")
        return {"message": "Password updated successfully"}

    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise