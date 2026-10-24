from app.schemas.common import Message, PaginatedResponse
from app.schemas.role import RoleBase, RoleCreate, RoleUpdate, RoleRead
from app.schemas.book_state import (
    BookStateBase,
    BookStateCreate,
    BookStateUpdate,
    BookStateRead,
)
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryRead,
)
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserRead, UserProfile
from app.schemas.book import BookBase, BookCreate, BookUpdate, BookRead
from app.schemas.transaction import (
    BorrowCreate,
    ReturnRequest,
    TransactionRead,
    TransactionActionResponse,
)
from app.schemas.auth import Token, TokenPayload, LoginRequest, RegisterRequest
from app.schemas.analytics import DashboardStats, CategoryBorrowStats, ReportItem

__all__ = [
    "Message",
    "PaginatedResponse",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "BookStateBase",
    "BookStateCreate",
    "BookStateUpdate",
    "BookStateRead",
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryRead",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserProfile",
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "BookRead",
    "BorrowCreate",
    "ReturnRequest",
    "TransactionRead",
    "TransactionActionResponse",
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "DashboardStats",
    "CategoryBorrowStats",
    "ReportItem",
]
