from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Category]:
        stmt = select(Category).where(func.lower(Category.name) == name.strip().lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_counts(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Category], int]:
        count_stmt = select(func.count(Category.id))
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = select(Category).order_by(Category.name.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        categories = list(result.scalars().all())
        return categories, total

    async def ensure_default_categories(self, db: AsyncSession) -> None:
        defaults = [
            "Fiction",
            "Non-Fiction",
            "Science",
            "History",
            "Philosophy",
            "Fantasy",
            "Children & Youth",
            "Technology",
            "Biography",
        ]
        for name in defaults:
            existing = await self.get_by_name(db, name)
            if not existing:
                cat = Category(name=name)
                db.add(cat)
        await db.commit()


crud_category = CRUDCategory(Category)
