from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_book import crud_book
from app.crud.crud_book_state import crud_book_state
from app.crud.crud_transaction import crud_transaction
from app.crud.crud_user import crud_user
from app.models.book_state import BookState, StateEnum
from app.models.role import RoleEnum
from app.models.transaction import BorrowingTransaction
from app.models.user import User
from app.schemas.transaction import BorrowCreate, ReturnRequest


class LoanService:
    """
    Business logic layer for handling Book Loans and Inventory Returns.
    Guarantees ACID transactions, strict role validation, and state transitions.
    """

    async def borrow_book(
        self,
        db: AsyncSession,
        borrow_in: BorrowCreate,
        handler: User,
    ) -> BorrowingTransaction:
        # 1. Verify borrowing member
        member = await crud_user.get_by_id(db, id=borrow_in.user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID {borrow_in.user_id} was not found.",
            )
        if not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot loan book to an inactive user account ({member.email}).",
            )

        # Enforce that borrower has the 'Member' role
        member_role_label = member.role.label if member.role else ""
        try:
            normalized_role = RoleEnum.normalize(member_role_label)
        except ValueError:
            normalized_role = member_role_label

        if (
            normalized_role != RoleEnum.MEMBER.value
            and normalized_role != RoleEnum.MEMBER
        ):
            # Allow Admin or Librarian to borrow if intended, but warn or validate
            # The requirement specifies: "Verify the member user exists and has a 'Member' role."
            # We strictly enforce Member role or staff borrowing
            if member_role_label not in [RoleEnum.MEMBER.value, "Membre"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Target user must have the 'Member' role to borrow books. "
                        f"Current user role: '{member_role_label}'"
                    ),
                )

        # 2. Verify physical book and availability
        book = await crud_book.get_by_id(db, id=borrow_in.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID {borrow_in.book_id} was not found.",
            )

        current_state_name = book.state.name if book.state else ""
        try:
            normalized_state = StateEnum.normalize(current_state_name)
        except ValueError:
            normalized_state = current_state_name

        if (
            normalized_state != StateEnum.AVAILABLE.value
            and normalized_state != StateEnum.AVAILABLE
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Book '{book.title}' (ID {book.id}) is not available for loan. "
                    f"Current condition state: '{current_state_name}'."
                ),
            )

        # Verify no unreturned loan collision
        active_loan = await crud_transaction.get_active_by_book_id(db, book_id=book.id)
        if active_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book '{book.title}' is already logged in an active loan (Transaction ID {active_loan.id}).",
            )

        # 3. Calculate due date (defaults to +14 days)
        now = datetime.now(timezone.utc)
        if borrow_in.return_due_date:
            # Ensure due date is timezone-aware
            due_date = borrow_in.return_due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            if due_date <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Return due date must be in the future.",
                )
        else:
            due_date = now + timedelta(days=14)

        # 4. Find 'Borrowed' state
        borrowed_state = await crud_book_state.get_by_name(db, StateEnum.BORROWED.value)
        if not borrowed_state:
            # Fallback to creating state if needed
            borrowed_state = await crud_book_state.create(
                db, {"name": StateEnum.BORROWED.value}
            )

        # 5. Atomic transaction execution
        try:
            # Toggle book state to Borrowed
            book.state_id = borrowed_state.id
            db.add(book)

            # Create loan transaction
            loan = BorrowingTransaction(
                user_id=member.id,
                book_id=book.id,
                borrow_date=now,
                return_due_date=due_date,
                actual_return_date=None,
                handler_id=handler.id,
                created_at=now,
            )
            db.add(loan)

            await db.commit()
            await db.refresh(loan)
            # Fetch with joined relationships
            return await crud_transaction.get_by_id(db, loan.id)  # type: ignore

        except Exception as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process borrowing loan: {str(exc)}",
            ) from exc

    async def return_book(
        self,
        db: AsyncSession,
        return_in: ReturnRequest,
        handler: User,
    ) -> Tuple[BorrowingTransaction, str]:
        # 1. Locate active transaction
        active_loan: Optional[BorrowingTransaction] = None

        if return_in.transaction_id:
            active_loan = await crud_transaction.get_active_by_id(
                db, transaction_id=return_in.transaction_id
            )
            if not active_loan:
                # Check if it was already returned
                existing = await crud_transaction.get_by_id(
                    db, id=return_in.transaction_id
                )
                if existing and existing.actual_return_date is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Transaction #{return_in.transaction_id} was already returned on "
                            f"{existing.actual_return_date.strftime('%Y-%m-%d %H:%M:%S')}."
                        ),
                    )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Active loan transaction #{return_in.transaction_id} not found.",
                )
        elif return_in.book_id:
            active_loan = await crud_transaction.get_active_by_book_id(
                db, book_id=return_in.book_id
            )
            if not active_loan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No active loan found for book ID {return_in.book_id}.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either 'book_id' or 'transaction_id' to return a book.",
            )

        # 2. Determine target return condition state
        target_state: Optional[BookState] = None
        if return_in.new_state_id:
            target_state = await crud_book_state.get(db, id=return_in.new_state_id)
            if not target_state:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target book state ID {return_in.new_state_id} not found.",
                )
        elif return_in.new_state_name:
            target_state = await crud_book_state.get_by_name(
                db, return_in.new_state_name
            )
            if not target_state:
                target_state = await crud_book_state.create(
                    db, {"name": return_in.new_state_name}
                )
        else:
            # Defaults back to 'Available'
            target_state = await crud_book_state.get_by_name(
                db, StateEnum.AVAILABLE.value
            )
            if not target_state:
                target_state = await crud_book_state.create(
                    db, {"name": StateEnum.AVAILABLE.value}
                )

        now = datetime.now(timezone.utc)

        # 3. Check if loan was returned late
        is_late = False
        days_late = 0
        due = active_loan.return_due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now > due:
            is_late = True
            days_late = (now - due).days

        # 4. Atomic transaction update
        try:
            # Update transaction return date
            active_loan.actual_return_date = now
            db.add(active_loan)

            # Update book condition state
            book = await crud_book.get(db, id=active_loan.book_id)
            if book:
                book.state_id = target_state.id
                db.add(book)

            await db.commit()
            await db.refresh(active_loan)

            feedback_msg = f"Book '{active_loan.book.title}' successfully returned into inventory as '{target_state.name}'."
            if is_late:
                feedback_msg += f" Note: Returned {days_late} day(s) overdue."

            refreshed = await crud_transaction.get_by_id(db, active_loan.id)
            return refreshed, feedback_msg  # type: ignore

        except Exception as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process book return: {str(exc)}",
            ) from exc


loan_service = LoanService()
