from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.book import Book
from app.models.transaction import BorrowingTransaction
from app.schemas.transaction import BorrowCreate


class CRUDTransaction(CRUDBase[BorrowingTransaction, BorrowCreate, dict]):
    async def get_by_id(
        self, db: AsyncSession, id: int
    ) -> Optional[BorrowingTransaction]:
        stmt = (
            select(BorrowingTransaction)
            .options(
                selectinload(BorrowingTransaction.borrower),
                selectinload(BorrowingTransaction.handler),
                selectinload(BorrowingTransaction.book).selectinload(Book.category),
                selectinload(BorrowingTransaction.book).selectinload(Book.state),
            )
            .where(BorrowingTransaction.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_book_id(
        self,
        db: AsyncSession,
        book_id: int,
    ) -> Optional[BorrowingTransaction]:
        stmt = (
            select(BorrowingTransaction)
            .options(
                selectinload(BorrowingTransaction.borrower),
                selectinload(BorrowingTransaction.handler),
                selectinload(BorrowingTransaction.book),
            )
            .where(
                BorrowingTransaction.book_id == book_id,
                BorrowingTransaction.actual_return_date.is_(None),
            )
            .order_by(BorrowingTransaction.id.desc())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_id(
        self,
        db: AsyncSession,
        transaction_id: int,
    ) -> Optional[BorrowingTransaction]:
        stmt = (
            select(BorrowingTransaction)
            .options(
                selectinload(BorrowingTransaction.borrower),
                selectinload(BorrowingTransaction.handler),
                selectinload(BorrowingTransaction.book),
            )
            .where(
                BorrowingTransaction.id == transaction_id,
                BorrowingTransaction.actual_return_date.is_(None),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        book_id: Optional[int] = None,
        status: Optional[str] = None,  # "active", "returned", "overdue"
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[BorrowingTransaction], int]:
        filters = []
        now = datetime.now(timezone.utc)

        if user_id is not None:
            filters.append(BorrowingTransaction.user_id == user_id)
        if book_id is not None:
            filters.append(BorrowingTransaction.book_id == book_id)

        if status:
            s = status.strip().lower()
            if s == "active":
                filters.append(BorrowingTransaction.actual_return_date.is_(None))
            elif s == "returned":
                filters.append(BorrowingTransaction.actual_return_date.is_not(None))
            elif s == "overdue":
                filters.append(BorrowingTransaction.actual_return_date.is_(None))
                filters.append(BorrowingTransaction.return_due_date < now)

        stmt = select(BorrowingTransaction).options(
            selectinload(BorrowingTransaction.borrower),
            selectinload(BorrowingTransaction.handler),
            selectinload(BorrowingTransaction.book).selectinload(Book.category),
            selectinload(BorrowingTransaction.book).selectinload(Book.state),
        )
        if filters:
            stmt = stmt.where(*filters)

        count_stmt = select(func.count(BorrowingTransaction.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(BorrowingTransaction.id.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        transactions = list(res.scalars().all())

        return transactions, total

    async def count_active_user_loans(self, db: AsyncSession, user_id: int) -> int:
        stmt = select(func.count(BorrowingTransaction.id)).where(
            BorrowingTransaction.user_id == user_id,
            BorrowingTransaction.actual_return_date.is_(None),
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def count_overdue_loans(self, db: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        stmt = select(func.count(BorrowingTransaction.id)).where(
            BorrowingTransaction.actual_return_date.is_(None),
            BorrowingTransaction.return_due_date < now,
        )
        res = await db.execute(stmt)
        return res.scalar() or 0


crud_transaction = CRUDTransaction(BorrowingTransaction)
