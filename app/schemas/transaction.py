from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.book import BookRead
from app.schemas.user import UserRead


class BorrowCreate(BaseModel):
    user_id: int = Field(..., description="ID of library member borrowing the book")
    book_id: int = Field(..., description="ID of the physical book to borrow")
    return_due_date: Optional[datetime] = Field(
        None,
        description="Due date for returning the book (defaults to +14 days if omitted)",
    )


class ReturnRequest(BaseModel):
    book_id: Optional[int] = Field(
        None, description="ID of the book to return (if transaction_id omitted)"
    )
    transaction_id: Optional[int] = Field(
        None, description="ID of the active loan transaction"
    )
    new_state_id: Optional[int] = Field(
        None,
        description="Optional condition state ID (defaults to 'Available', e.g. set to 'Damaged' if returned damaged)",
    )
    new_state_name: Optional[str] = Field(
        None,
        description="Optional state name ('Available', 'Damaged', 'Lost')",
    )


class TransactionRead(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime
    return_due_date: datetime
    actual_return_date: Optional[datetime] = None
    handler_id: Optional[int] = None
    created_at: datetime
    is_active: bool
    is_overdue: bool
    borrower: Optional[UserRead] = None
    handler: Optional[UserRead] = None
    book: Optional[BookRead] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionActionResponse(BaseModel):
    message: str
    transaction: TransactionRead
