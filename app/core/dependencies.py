import logging
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.role import RoleEnum
from app.models.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True,
)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate JWT access token and return the authenticated User from database.
    Raises HTTP 401 if token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # Query user with eagerly loaded role
    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify that the authenticated user account is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated or suspended.",
        )
    return current_user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that the active user possesses one of the specified allowed roles.
    Supports normalized role strings (e.g., 'Administrator', 'Librarian', 'Member').
    """
    # Normalize expected allowed roles to RoleEnum values if possible
    normalized_allowed = []
    for r in allowed_roles:
        try:
            normalized_allowed.append(RoleEnum.normalize(r).value)
        except ValueError:
            normalized_allowed.append(r)

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role_label = current_user.role.label if current_user.role else ""
        try:
            normalized_user_role = RoleEnum.normalize(user_role_label).value
        except ValueError:
            normalized_user_role = user_role_label

        if normalized_user_role not in normalized_allowed:
            logger.warning(
                f"Access denied for user {current_user.email} (role: {user_role_label}). "
                f"Required one of: {normalized_allowed}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Forbidden: You do not have permission to perform this action. "
                    f"Required roles: {allowed_roles}. Current role: '{user_role_label}'"
                ),
            )
        return current_user

    return role_checker


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency for endpoints open to public or enhanced for members.
    """
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
