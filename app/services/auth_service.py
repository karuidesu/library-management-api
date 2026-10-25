import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.crud.crud_book_state import crud_book_state
from app.crud.crud_category import crud_category
from app.crud.crud_role import crud_role
from app.crud.crud_user import crud_user
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserCreate, UserRead

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication & Identity Management Service.
    Handles login, token issuance, registration, and initial system bootstrapping.
    """

    async def authenticate_and_create_token(
        self,
        db: AsyncSession,
        login_in: LoginRequest,
    ) -> Token:
        user = await crud_user.authenticate(
            db, email=login_in.email, password=login_in.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive or disabled.",
            )

        # Update last access timestamp
        await crud_user.update_last_access(db, user)

        role_label = user.role.label if user.role else RoleEnum.MEMBER.value
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": role_label, "email": user.email},
        )

        user_read = UserRead.model_validate(user)
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_read,
        )

    async def register_new_user(
        self,
        db: AsyncSession,
        register_in: RegisterRequest,
        current_admin_user: Optional[User] = None,
    ) -> UserRead:
        # Check if email is already taken
        existing_user = await crud_user.get_by_email(db, email=register_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # Determine role
        # Requirement: "Admin creates staff, but standard signup puts users into a 'Member' state"
        assigned_role_id: int
        if register_in.role_id and current_admin_user:
            # Verify caller is an Administrator
            caller_role = (
                current_admin_user.role.label if current_admin_user.role else ""
            )
            if (
                caller_role != RoleEnum.ADMINISTRATOR.value
                and caller_role != "Administrator"
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Administrators can assign custom roles during account creation.",
                )
            target_role = await crud_role.get(db, id=register_in.role_id)
            if not target_role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role ID {register_in.role_id} not found.",
                )
            assigned_role_id = target_role.id
        else:
            # Default to Member role
            member_role = await crud_role.get_by_label(db, RoleEnum.MEMBER.value)
            if not member_role:
                member_role = await crud_role.create(
                    db, {"label": RoleEnum.MEMBER.value}
                )
            assigned_role_id = member_role.id

        user_create = UserCreate(
            name=register_in.name,
            email=register_in.email,
            password=register_in.password,
            role_id=assigned_role_id,
        )

        new_user = await crud_user.create(
            db, obj_in=user_create, role_id=assigned_role_id
        )
        return UserRead.model_validate(new_user)

    async def bootstrap_initial_data(self, db: AsyncSession) -> None:
        """
        Gracefully populates standard system roles, book states, default categories,
        and seeds the initial Administrator user if none exists.
        """
        logger.info("Verifying and bootstrapping initial database records...")
        # 1. Roles
        await crud_role.ensure_roles(db)

        # 2. Book States
        await crud_book_state.ensure_states(db)

        # 3. Categories
        await crud_category.ensure_default_categories(db)

        # 4. Superuser
        admin_role = await crud_role.get_by_label(db, RoleEnum.ADMINISTRATOR.value)
        if admin_role:
            admin_user = await crud_user.get_by_email(
                db, email=settings.FIRST_SUPERUSER_EMAIL
            )
            if not admin_user:
                logger.info(
                    f"Seeding default superuser: {settings.FIRST_SUPERUSER_EMAIL}"
                )
                await crud_user.create(
                    db,
                    obj_in={
                        "name": settings.FIRST_SUPERUSER_NAME,
                        "email": settings.FIRST_SUPERUSER_EMAIL,
                        "password": settings.FIRST_SUPERUSER_PASSWORD,
                        "is_active": True,
                        "role_id": admin_role.id,
                    },
                    role_id=admin_role.id,
                )
        logger.info("Database bootstrap completed successfully.")


auth_service = AuthService()
