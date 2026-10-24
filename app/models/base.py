from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Returns current datetime in UTC."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Mixin that adds created_at timestamp to models.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
