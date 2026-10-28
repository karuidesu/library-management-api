from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.book import Book
from app.models.book_state import BookState
from app.models.category import Category
from app.schemas.book import BookCreate, BookUpdate


class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[Book]:
        stmt = (
            select(Book)
            .options(selectinload(Book.category), selectinload(Book.state))
            .where(Book.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_isbn(self, db: AsyncSession, isbn: str) -> Optional[Book]:
        clean_isbn = isbn.replace("-", "").replace(" ", "").upper()
        stmt = (
            select(Book)
            .options(selectinload(Book.category), selectinload(Book.state))
            .where(
                func.replace(func.replace(Book.isbn, "-", ""), " ", "") == clean_isbn
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        obj_in: Union[BookCreate, Dict[str, Any]],
        default_state_id: Optional[int] = None,
    ) -> Book:
        if isinstance(obj_in, dict):
            data = obj_in.copy()
        else:
            data = obj_in.model_dump(exclude_unset=True)

        if "state_id" not in data or data["state_id"] is None:
            if default_state_id is not None:
                data["state_id"] = default_state_id

        db_obj = Book(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return await self.get_by_id(db, db_obj.id)  # type: ignore

    async def search(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        category_id: Optional[int] = None,
        category_name: Optional[str] = None,
        state_id: Optional[int] = None,
        state_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Book], int]:
        filters = []

        if search:
            q = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(Book.title).like(q),
                    func.lower(Book.author).like(q),
                    func.lower(Book.isbn).like(q),
                )
            )
        if title:
            filters.append(func.lower(Book.title).like(f"%{title.strip().lower()}%"))
        if author:
            filters.append(func.lower(Book.author).like(f"%{author.strip().lower()}%"))
        if isbn:
            clean_search_isbn = isbn.replace("-", "").replace(" ", "").upper()
            filters.append(
                func.replace(func.replace(Book.isbn, "-", ""), " ", "").like(
                    f"%{clean_search_isbn}%"
                )
            )
        if category_id is not None:
            filters.append(Book.category_id == category_id)
        if state_id is not None:
            filters.append(Book.state_id == state_id)

        stmt = (
            select(Book)
            .join(Category, Book.category_id == Category.id)
            .join(BookState, Book.state_id == BookState.id)
            .options(selectinload(Book.category), selectinload(Book.state))
        )

        if category_name:
            filters.append(func.lower(Category.name) == category_name.strip().lower())
        if state_name:
            filters.append(func.lower(BookState.name) == state_name.strip().lower())

        if filters:
            stmt = stmt.where(*filters)

        # Count total
        count_stmt = (
            select(func.count(Book.id))
            .join(Category, Book.category_id == Category.id)
            .join(BookState, Book.state_id == BookState.id)
        )
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        # Execute pagination
        stmt = stmt.order_by(Book.id.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        books = list(res.scalars().all())

        return books, total

    async def is_borrowed(self, db: AsyncSession, book_id: int) -> bool:
        stmt = (
            select(BookState.name)
            .join(Book, Book.state_id == BookState.id)
            .where(Book.id == book_id)
        )
        res = await db.execute(stmt)
        state_name = res.scalar_one_or_none()
        if not state_name:
            return False
        return state_name.lower() in ("borrowed", "emprunté", "emprunte")


crud_book = CRUDBook(Book)
