from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator

class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserLoginWithRole(UserLogin):
    role: UserRole

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.user

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    @validator("password")
    def password_complexity(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)