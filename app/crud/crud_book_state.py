from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.book_state import BookState, StateEnum
from app.schemas.book_state import BookStateCreate, BookStateUpdate


class CRUDBookState(CRUDBase[BookState, BookStateCreate, BookStateUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[BookState]:
        stmt = select(BookState).where(
            func.lower(BookState.name) == name.strip().lower()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_states(self, db: AsyncSession) -> None:
        """
        Gracefully populates standard book condition states.
        """
        standard_states = [
            StateEnum.AVAILABLE.value,
            StateEnum.BORROWED.value,
            StateEnum.DAMAGED.value,
            StateEnum.LOST.value,
        ]
        for state_name in standard_states:
            existing = await self.get_by_name(db, state_name)
            if not existing:
                state = BookState(name=state_name)
                db.add(state)
        await db.commit()


crud_book_state = CRUDBookState(BookState)
