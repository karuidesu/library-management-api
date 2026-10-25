from enum import Enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.user import User


class RoleEnum(str, Enum):
    ADMINISTRATOR = "Administrator"
    LIBRARIAN = "Librarian"
    MEMBER = "Member"

    @classmethod
    def normalize(cls, val: str) -> "RoleEnum":
        """
        Normalize role string from multiple variations (e.g., Admin, Bibliothécaire, Membre).
        """
        v = val.strip().lower()
        if v in ("administrator", "admin", "administrateur"):
            return cls.ADMINISTRATOR
        elif v in ("librarian", "bibliothécaire", "bibliothecaire", "staff"):
            return cls.LIBRARIAN
        elif v in ("member", "membre", "user", "adherent"):
            return cls.MEMBER
        raise ValueError(f"Unknown role: {val}")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    label: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, label='{self.label}')>"
