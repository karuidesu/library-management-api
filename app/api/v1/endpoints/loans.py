import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.crud.crud_transaction import crud_transaction
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import (
    BorrowCreate,
    ReturnRequest,
    TransactionActionResponse,
    TransactionRead,
)
from app.services.loan_service import loan_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TransactionRead],
    summary="List borrowing transactions",
    description=(
        "Retrieve loan transactions with filtering. "
        "Administrators and Librarians can see all loans. "
        "Standard Members can view only their own borrowing history."
    ),
)
async def read_loans(
    user_id: Optional[int] = Query(None, description="Filter by member ID"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    status: Optional[str] = Query(
        None, description="Filter status: 'active', 'returned', or 'overdue'"
    ),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[TransactionRead]:
    caller_role = current_user.role.label if current_user.role else ""
    is_staff = caller_role in [RoleEnum.ADMINISTRATOR.value, RoleEnum.LIBRARIAN.value]

    # If member, force filter to their own user_id
    effective_user_id = user_id if is_staff else current_user.id

    txs, total = await crud_transaction.search(
        db=db,
        user_id=effective_user_id,
        book_id=book_id,
        status=status,
        skip=offset,
        limit=limit,
    )

    items = [TransactionRead.model_validate(t) for t in txs]
    pages = math.ceil(total / limit) if limit > 0 else 1

    return PaginatedResponse[TransactionRead](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        pages=pages,
    )


@router.get(
    "/{id}",
    response_model=TransactionRead,
    summary="Get loan transaction details",
    description="Retrieve a single loan record. Members can only view their own transactions.",
)
async def read_loan(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionRead:
    tx = await crud_transaction.get_by_id(db, id=id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {id} was not found.",
        )

    caller_role = current_user.role.label if current_user.role else ""
    is_staff = caller_role in [RoleEnum.ADMINISTRATOR.value, RoleEnum.LIBRARIAN.value]

    if not is_staff and tx.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this loan transaction.",
        )

    return TransactionRead.model_validate(tx)


@router.post(
    "/borrow",
    response_model=TransactionActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow a book (Loan checkout)",
    description=(
        "Registers a loan for an available book to a library member. "
        "Validates member existence & role, verifies book availability, "
        "creates loan record, and sets book state to 'Borrowed'. "
        "Restricted to Administrator and Librarian."
    ),
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def borrow_book(
    borrow_in: BorrowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionActionResponse:
    tx = await loan_service.borrow_book(
        db=db,
        borrow_in=borrow_in,
        handler=current_user,
    )
    tx_read = TransactionRead.model_validate(tx)
    return TransactionActionResponse(
        message=f"Book '{tx.book.title}' successfully loaned to member '{tx.borrower.name}'. Due date: {tx.return_due_date.strftime('%Y-%m-%d')}.",
        transaction=tx_read,
    )


@router.post(
    "/return",
    response_model=TransactionActionResponse,
    summary="Return a book (Loan check-in)",
    description=(
        "Checks in a borrowed book. Finds active loan, records actual return date, "
        "and resets book condition state back to 'Available' (or 'Damaged'/'Lost'). "
        "Restricted to Administrator and Librarian."
    ),
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def return_book(
    return_in: ReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TransactionActionResponse:
    tx, feedback = await loan_service.return_book(
        db=db,
        return_in=return_in,
        handler=current_user,
    )
    tx_read = TransactionRead.model_validate(tx)
    return TransactionActionResponse(
        message=feedback,
        transaction=tx_read,
    )
