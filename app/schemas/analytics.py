from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_books: int
    active_members: int
    borrowed_books: int
    overdue_loans: int
    total_categories: int
    recent_activities: List[Dict[str, Any]] = []


class CategoryBorrowStats(BaseModel):
    category_id: int
    category_name: str
    total_books: int
    borrow_count: int
    active_loans: int


class ReportItem(BaseModel):
    transaction_id: int
    borrow_date: datetime
    return_due_date: datetime
    actual_return_date: Optional[datetime] = None
    status: str
    member_id: int
    member_name: str
    member_email: str
    book_id: int
    book_title: str
    book_isbn: str
    category_name: str
    handler_name: Optional[str] = None
