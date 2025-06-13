from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from fastapi import HTTPException, status

from app.core.config import settings
from app.exception import InvalidTokenError

def generate_password_reset_token(email: str) -> str:
    delta = timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except jwt.JWTError:
        raise InvalidTokenError()