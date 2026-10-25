from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role_id: Optional[int] = Field(None, description="Staff creation role (Admin only)")
