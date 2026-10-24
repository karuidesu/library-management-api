"""Initial Agbale Library Management schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-14 10:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_label"), "roles", ["label"], unique=True)

    # 2. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashedPassword", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_access", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_name"), "users", ["name"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)

    # 3. Categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)

    # 4. Book States table
    op.create_table(
        "book_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_book_states_id"), "book_states", ["id"], unique=False)
    op.create_index(op.f("ix_book_states_name"), "book_states", ["name"], unique=True)

    # 5. Books table
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("copies", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("cover_color", sa.String(length=100), nullable=True),
        sa.Column("cover_accent", sa.String(length=50), nullable=True),
        sa.Column("cover_emoji", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["state_id"], ["book_states.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_books_author"), "books", ["author"], unique=False)
    op.create_index(
        op.f("ix_books_category_id"), "books", ["category_id"], unique=False
    )
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)
    op.create_index(op.f("ix_books_isbn"), "books", ["isbn"], unique=True)
    op.create_index(op.f("ix_books_state_id"), "books", ["state_id"], unique=False)
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)

    # 6. Borrowing Transactions table
    op.create_table(
        "borrowing_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("borrow_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("return_due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handler_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["handler_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_borrowing_transactions_actual_return_date"),
        "borrowing_transactions",
        ["actual_return_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_borrowing_transactions_book_id"),
        "borrowing_transactions",
        ["book_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_borrowing_transactions_handler_id"),
        "borrowing_transactions",
        ["handler_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_borrowing_transactions_id"),
        "borrowing_transactions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_borrowing_transactions_return_due_date"),
        "borrowing_transactions",
        ["return_due_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_borrowing_transactions_user_id"),
        "borrowing_transactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("borrowing_transactions")
    op.drop_table("books")
    op.drop_table("book_states")
    op.drop_table("categories")
    op.drop_table("users")
    op.drop_table("roles")
