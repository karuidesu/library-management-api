from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryRead
from app.schemas.book_state import BookStateRead


def validate_isbn_integrity(isbn_str: str) -> str:
    """
    Validate ISBN-10 or ISBN-13 checksum integrity according to standard algorithms.
    Raises ValueError on checksum or format mismatch.
    """
    cleaned = re.sub(r"[-\s]", "", isbn_str.strip().upper())

    if len(cleaned) == 10:
        # Validate ISBN-10
        if not re.match(r"^\d{9}[\dX]$", cleaned):
            raise ValueError(
                f"Invalid ISBN-10 characters: '{isbn_str}'. Must be 9 digits followed by digit or 'X'."
            )

        checksum = 0
        for i, char in enumerate(cleaned):
            weight = 10 - i
            val = 10 if char == "X" else int(char)
            checksum += weight * val

        if checksum % 11 != 0:
            raise ValueError(f"ISBN-10 checksum validation failed for: '{isbn_str}'.")
        return cleaned

    elif len(cleaned) == 13:
        # Validate ISBN-13
        if not re.match(r"^\d{13}$", cleaned):
            raise ValueError(
                f"Invalid ISBN-13 characters: '{isbn_str}'. Must be exactly 13 digits."
            )

        checksum = 0
        for i, char in enumerate(cleaned):
            weight = 1 if i % 2 == 0 else 3
            checksum += weight * int(char)

        if checksum % 10 != 0:
            raise ValueError(f"ISBN-13 checksum validation failed for: '{isbn_str}'.")
        return cleaned
    else:
        raise ValueError(
            f"Invalid ISBN length ({len(cleaned)} chars). ISBN must be either 10 or 13 digits (excluding hyphens)."
        )


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Author name")
    isbn: str = Field(..., description="Valid ISBN-10 or ISBN-13 with integrity check")
    category_id: int = Field(..., description="Category foreign key identifier")
    state_id: Optional[int] = Field(
        None, description="Condition state ID (defaults to Available)"
    )
    description: Optional[str] = Field(None, description="Synopsis or summary")
    publication_year: Optional[int] = Field(
        None, ge=1000, le=2100, description="Year of publication"
    )
    copies: int = Field(default=1, ge=1, description="Total physical inventory copies")
    cover_color: Optional[str] = Field(
        None, description="Cover background gradient or color"
    )
    cover_accent: Optional[str] = Field(None, description="Cover accent hex code")
    cover_emoji: Optional[str] = Field(None, description="Cover decorative icon/emoji")

    @field_validator("isbn")
    @classmethod
    def check_isbn(cls, v: str) -> str:
        return validate_isbn_integrity(v)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = None
    category_id: Optional[int] = None
    state_id: Optional[int] = None
    description: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    copies: Optional[int] = Field(None, ge=1)
    cover_color: Optional[str] = None
    cover_accent: Optional[str] = None
    cover_emoji: Optional[str] = None

    @field_validator("isbn")
    @classmethod
    def check_isbn(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_isbn_integrity(v)
        return v


class BookRead(BookBase):
    id: int
    state_id: int
    created_at: datetime
    category: Optional[CategoryRead] = None
    state: Optional[BookStateRead] = None
    is_borrowed: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
