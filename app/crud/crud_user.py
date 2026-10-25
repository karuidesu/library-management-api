from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[User]:
        stmt = select(User).options(selectinload(User.role)).where(User.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(func.lower(User.email) == email.strip().lower())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashedPassword):
            return None
        return user

    async def update_last_access(self, db: AsyncSession, user: User) -> User:
        user.last_access = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def create(
        self,
        db: AsyncSession,
        obj_in: Union[UserCreate, Dict[str, Any]],
        role_id: Optional[int] = None,
    ) -> User:
        if isinstance(obj_in, dict):
            data = obj_in.copy()
            plain_pwd = data.pop("password", None)
            assigned_role_id = role_id or data.pop("role_id", None)
            name = data.get("name", "")
            email = data.get("email", "")
            is_active = data.get("is_active", True)
        else:
            data = obj_in.model_dump(exclude_unset=True)
            plain_pwd = data.pop("password", None)
            assigned_role_id = role_id or data.pop("role_id", None)
            name = obj_in.name
            email = obj_in.email
            is_active = obj_in.is_active

        hashed_pwd = get_password_hash(plain_pwd) if plain_pwd else ""
        db_user = User(
            name=name,
            email=email.strip().lower(),
            hashedPassword=hashed_pwd,
            is_active=is_active,
            role_id=assigned_role_id,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        # Load joined role
        return await self.get_by_id(db, db_user.id)  # type: ignore

    async def update_user(
        self,
        db: AsyncSession,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            db_obj.hashedPassword = get_password_hash(update_data["password"])
            del update_data["password"]

        if "email" in update_data and update_data["email"]:
            db_obj.email = update_data["email"].strip().lower()
            del update_data["email"]

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return await self.get_by_id(db, db_obj.id)  # type: ignore

    async def search(
        self,
        db: AsyncSession,
        query: Optional[str] = None,
        name: Optional[str] = None,
        role_id: Optional[int] = None,
        role_label: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[User], int]:
        filters = []

        if query:
            q = f"%{query.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(User.name).like(q),
                    func.lower(User.email).like(q),
                )
            )
        if name:
            filters.append(func.lower(User.name).like(f"%{name.strip().lower()}%"))
        if role_id is not None:
            filters.append(User.role_id == role_id)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        # Base statement
        stmt = (
            select(User)
            .join(Role, User.role_id == Role.id)
            .options(selectinload(User.role))
        )
        if role_label:
            filters.append(func.lower(Role.label) == role_label.strip().lower())

        if filters:
            stmt = stmt.where(*filters)

        # Count total matches
        count_stmt = select(func.count(User.id)).join(Role, User.role_id == Role.id)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        # Execute pagination
        stmt = stmt.order_by(User.id.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        users = list(res.scalars().all())

        return users, total


crud_user = CRUDUser(User)
