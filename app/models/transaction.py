from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class BorrowingTransaction(Base, TimestampMixin):
    __tablename__ = "borrowing_transactions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("books.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    borrow_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    return_due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    actual_return_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    handler_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    borrower: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="borrowed_transactions",
        lazy="joined",
    )
    handler: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[handler_id],
        back_populates="handled_transactions",
        lazy="joined",
    )
    book: Mapped["Book"] = relationship(
        "Book",
        foreign_keys=[book_id],
        back_populates="borrowing_transactions",
        lazy="joined",
    )

    @property
    def is_active(self) -> bool:
        return self.actual_return_date is None

    @property
    def is_overdue(self) -> bool:
        if self.actual_return_date is not None:
            return False
        return datetime.now(self.return_due_date.tzinfo or None) > self.return_due_date

    def __repr__(self) -> str:
        return (
            f"<BorrowingTransaction(id={self.id}, user_id={self.user_id}, "
            f"book_id={self.book_id}, return_due_date='{self.return_due_date}')>"
        )
