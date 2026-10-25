from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.role import Role, RoleEnum
from app.schemas.role import RoleCreate, RoleUpdate


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    async def get_by_label(self, db: AsyncSession, label: str) -> Optional[Role]:
        stmt = select(Role).where(func.lower(Role.label) == label.strip().lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_roles(self, db: AsyncSession) -> None:
        """
        Gracefully populates standard system roles if not present.
        """
        standard_roles = [
            RoleEnum.ADMINISTRATOR.value,
            RoleEnum.LIBRARIAN.value,
            RoleEnum.MEMBER.value,
        ]
        for role_label in standard_roles:
            existing = await self.get_by_label(db, role_label)
            if not existing:
                role = Role(label=role_label)
                db.add(role)
        await db.commit()


crud_role = CRUDRole(Role)
