import csv
from datetime import datetime, timezone
import io
from typing import Any, Dict, List
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.book_state import BookState, StateEnum
from app.models.category import Category
from app.models.role import Role, RoleEnum
from app.models.transaction import BorrowingTransaction
from app.models.user import User
from app.schemas.analytics import CategoryBorrowStats, DashboardStats, ReportItem


class AnalyticsService:
    """
    Analytics and Business Intelligence Service.
    Aggregates library inventory metrics, circulation turnover, and audit reports.
    """

    async def get_dashboard_stats(self, db: AsyncSession) -> DashboardStats:
        now = datetime.now(timezone.utc)

        # 1. Total Books count
        stmt_books = select(func.count(Book.id))
        res_books = await db.execute(stmt_books)
        total_books = res_books.scalar() or 0

        # 2. Active Members count
        stmt_members = (
            select(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .where(
                User.is_active,
                func.lower(Role.label).in_([RoleEnum.MEMBER.value.lower(), "membre"]),
            )
        )
        res_members = await db.execute(stmt_members)
        active_members = res_members.scalar() or 0

        # 3. Borrowed Books count
        stmt_borrowed = (
            select(func.count(Book.id))
            .join(BookState, Book.state_id == BookState.id)
            .where(
                func.lower(BookState.name).in_(
                    [StateEnum.BORROWED.value.lower(), "emprunté", "emprunte"]
                )
            )
        )
        res_borrowed = await db.execute(stmt_borrowed)
        borrowed_books = res_borrowed.scalar() or 0

        # 4. Overdue Loans count
        stmt_overdue = select(func.count(BorrowingTransaction.id)).where(
            BorrowingTransaction.actual_return_date.is_(None),
            BorrowingTransaction.return_due_date < now,
        )
        res_overdue = await db.execute(stmt_overdue)
        overdue_loans = res_overdue.scalar() or 0

        # 5. Total Categories
        stmt_cats = select(func.count(Category.id))
        res_cats = await db.execute(stmt_cats)
        total_categories = res_cats.scalar() or 0

        # 6. Recent activity (last 10 events)
        stmt_recent = (
            select(BorrowingTransaction)
            .options(
                selectinload(BorrowingTransaction.borrower),
                selectinload(BorrowingTransaction.book),
            )
            .order_by(BorrowingTransaction.id.desc())
            .limit(10)
        )
        res_recent = await db.execute(stmt_recent)
        recent_txs = list(res_recent.scalars().all())

        recent_activities: List[Dict[str, Any]] = []
        for tx in recent_txs:
            action_type = "Returned" if tx.actual_return_date else "Borrowed"
            status_label = (
                "Returned"
                if tx.actual_return_date
                else ("Overdue" if tx.is_overdue else "In Progress")
            )
            recent_activities.append(
                {
                    "id": tx.id,
                    "action": action_type,
                    "book_id": tx.book_id,
                    "book_title": tx.book.title if tx.book else "Unknown",
                    "member_id": tx.user_id,
                    "member_name": tx.borrower.name if tx.borrower else "Unknown",
                    "date": (tx.actual_return_date or tx.borrow_date).isoformat(),
                    "status": status_label,
                }
            )

        return DashboardStats(
            total_books=total_books,
            active_members=active_members,
            borrowed_books=borrowed_books,
            overdue_loans=overdue_loans,
            total_categories=total_categories,
            recent_activities=recent_activities,
        )

    async def get_category_borrow_stats(
        self, db: AsyncSession
    ) -> List[CategoryBorrowStats]:
        """
        Calculates categorical borrowing frequency counts and ranking.
        """
        # Fetch all categories
        stmt_cats = select(Category).order_by(Category.name.asc())
        res_cats = await db.execute(stmt_cats)
        categories = list(res_cats.scalars().all())

        stats: List[CategoryBorrowStats] = []
        for cat in categories:
            # Count total books in this category
            stmt_books = select(func.count(Book.id)).where(Book.category_id == cat.id)
            res_books = await db.execute(stmt_books)
            total_books = res_books.scalar() or 0

            # Count total historical borrowings in this category
            stmt_borrow = (
                select(func.count(BorrowingTransaction.id))
                .join(Book, BorrowingTransaction.book_id == Book.id)
                .where(Book.category_id == cat.id)
            )
            res_borrow = await db.execute(stmt_borrow)
            borrow_count = res_borrow.scalar() or 0

            # Count current active loans in this category
            stmt_active = (
                select(func.count(BorrowingTransaction.id))
                .join(Book, BorrowingTransaction.book_id == Book.id)
                .where(
                    Book.category_id == cat.id,
                    BorrowingTransaction.actual_return_date.is_(None),
                )
            )
            res_active = await db.execute(stmt_active)
            active_loans = res_active.scalar() or 0

            stats.append(
                CategoryBorrowStats(
                    category_id=cat.id,
                    category_name=cat.name,
                    total_books=total_books,
                    borrow_count=borrow_count,
                    active_loans=active_loans,
                )
            )

        # Sort descending by borrowing frequency
        stats.sort(key=lambda s: s.borrow_count, reverse=True)
        return stats

    async def get_audit_reports(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[ReportItem]:
        """
        Retrieves historical audit list logs for all borrowing transactions.
        """
        stmt = (
            select(BorrowingTransaction)
            .options(
                selectinload(BorrowingTransaction.borrower),
                selectinload(BorrowingTransaction.handler),
                selectinload(BorrowingTransaction.book).selectinload(Book.category),
            )
            .order_by(BorrowingTransaction.id.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        txs = list(res.scalars().all())

        reports: List[ReportItem] = []
        for tx in txs:
            if tx.actual_return_date:
                status_str = "Returned"
            elif tx.is_overdue:
                status_str = "Overdue"
            else:
                status_str = "Active"

            reports.append(
                ReportItem(
                    transaction_id=tx.id,
                    borrow_date=tx.borrow_date,
                    return_due_date=tx.return_due_date,
                    actual_return_date=tx.actual_return_date,
                    status=status_str,
                    member_id=tx.user_id,
                    member_name=tx.borrower.name if tx.borrower else "Unknown",
                    member_email=tx.borrower.email if tx.borrower else "Unknown",
                    book_id=tx.book_id,
                    book_title=tx.book.title if tx.book else "Unknown",
                    book_isbn=tx.book.isbn if tx.book else "Unknown",
                    category_name=(
                        tx.book.category.name
                        if tx.book and tx.book.category
                        else "Uncategorized"
                    ),
                    handler_name=tx.handler.name if tx.handler else "System",
                )
            )

        return reports

    def export_reports_to_csv(self, reports: List[ReportItem]) -> str:
        """
        Converts audit report items into CSV formatted string.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow(
            [
                "Transaction ID",
                "Status",
                "Borrow Date (UTC)",
                "Due Date (UTC)",
                "Actual Return Date (UTC)",
                "Member ID",
                "Member Name",
                "Member Email",
                "Book ID",
                "Book Title",
                "Book ISBN",
                "Category",
                "Handler Name",
            ]
        )

        for r in reports:
            writer.writerow(
                [
                    r.transaction_id,
                    r.status,
                    r.borrow_date.strftime("%Y-%m-%d %H:%M:%S"),
                    r.return_due_date.strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        r.actual_return_date.strftime("%Y-%m-%d %H:%M:%S")
                        if r.actual_return_date
                        else "N/A"
                    ),
                    r.member_id,
                    r.member_name,
                    r.member_email,
                    r.book_id,
                    r.book_title,
                    r.book_isbn,
                    r.category_name,
                    r.handler_name or "N/A",
                ]
            )

        return output.getvalue()


analytics_service = AnalyticsService()
