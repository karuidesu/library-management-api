from enum import Enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.book import Book


class StateEnum(str, Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    DAMAGED = "Damaged"
    LOST = "Lost"

    @classmethod
    def normalize(cls, val: str) -> "StateEnum":
        v = val.strip().lower()
        if v in ("available", "disponible"):
            return cls.AVAILABLE
        elif v in ("borrowed", "emprunté", "emprunte"):
            return cls.BORROWED
        elif v in ("damaged", "endommagé", "endommage"):
            return cls.DAMAGED
        elif v in ("lost", "perdu"):
            return cls.LOST
        raise ValueError(f"Unknown book state: {val}")


class BookState(Base):
    __tablename__ = "book_states"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book",
        back_populates="state",
    )

    def __repr__(self) -> str:
        return f"<BookState(id={self.id}, name='{self.name}')>"
