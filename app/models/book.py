from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.book_state import BookState
    from app.models.transaction import BorrowingTransaction


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    state_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("book_states.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Optional / metadata fields for UI integration
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cover_color: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cover_accent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cover_emoji: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="books",
        lazy="joined",
    )
    state: Mapped["BookState"] = relationship(
        "BookState",
        back_populates="books",
        lazy="joined",
    )
    borrowing_transactions: Mapped[List["BorrowingTransaction"]] = relationship(
        "BorrowingTransaction",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
