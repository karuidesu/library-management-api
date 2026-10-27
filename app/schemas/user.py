from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleRead


class UserBase(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=120, description="Full name of the user"
    )
    email: EmailStr = Field(..., description="Valid unique email address")
    is_active: bool = Field(default=True, description="Account active status")


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=6, max_length=100, description="Plaintext password"
    )
    role_id: Optional[int] = Field(
        None, description="Assigned role ID (Admin only, defaults to Member)"
    )
    role: Optional[str] = Field(
        None, description="Optional role name if role_id not supplied"
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UserRead(UserBase):
    id: int
    role_id: int
    created_at: datetime
    last_access: Optional[datetime] = None
    role: Optional[RoleRead] = None
    active_loans_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserRead):
    pass
