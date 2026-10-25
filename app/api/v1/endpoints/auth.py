from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_optional_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserRead
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="User Login (OAuth2 Form / Swagger UI compatible)",
    description="Authenticates with email and password via OAuth2 standard form and returns a JWT access token.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    login_in = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.authenticate_and_create_token(db=db, login_in=login_in)


@router.post(
    "/login-json",
    response_model=Token,
    summary="User Login via JSON Body",
    description="Authenticates with JSON body containing email and password, returning a JWT access token.",
)
async def login_json(
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    return await auth_service.authenticate_and_create_token(db=db, login_in=login_in)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new User Account",
    description=(
        "Standard signup assigns the 'Member' role. "
        "If called by an authenticated Administrator with role_id specified, creates staff accounts."
    ),
)
async def register(
    register_in: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> UserRead:
    return await auth_service.register_new_user(
        db=db,
        register_in=register_in,
        current_admin_user=current_user,
    )
