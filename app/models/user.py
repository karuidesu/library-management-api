from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.transaction import BorrowingTransaction


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashedPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    last_access: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=utc_now,
    )

    # Alias property for Pythonic snake_case
    @property
    def hashed_password(self) -> str:
        return self.hashedPassword

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        self.hashedPassword = value

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")

    borrowed_transactions: Mapped[List["BorrowingTransaction"]] = relationship(
        "BorrowingTransaction",
        foreign_keys="BorrowingTransaction.user_id",
        back_populates="borrower",
        cascade="all, delete-orphan",
    )

    handled_transactions: Mapped[List["BorrowingTransaction"]] = relationship(
        "BorrowingTransaction",
        foreign_keys="BorrowingTransaction.handler_id",
        back_populates="handler",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', role_id={self.role_id})>"
