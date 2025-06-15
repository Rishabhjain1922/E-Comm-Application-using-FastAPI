from pydantic_settings import BaseSettings
from pydantic import EmailStr, Field
from typing import Optional

class Settings(BaseSettings):
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Database
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./ecommerce.db"

    # Email
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[EmailStr] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
