import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import require_roles
from app.crud.crud_book import crud_book
from app.crud.crud_book_state import crud_book_state
from app.crud.crud_category import crud_category
from app.crud.crud_transaction import crud_transaction
from app.models.book_state import StateEnum
from app.schemas.book import BookCreate, BookRead, BookUpdate
from app.schemas.common import Message, PaginatedResponse

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[BookRead],
    summary="List and filter books",
    description=(
        "Public or authenticated catalog search. Filter by title, author, ISBN, category, or state. "
        "Supports full pagination."
    ),
)
async def read_books(
    search: Optional[str] = Query(
        None, description="Global text search across title, author, or ISBN"
    ),
    title: Optional[str] = Query(None, description="Filter specifically by book title"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    isbn: Optional[str] = Query(None, description="Filter by ISBN"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    state_id: Optional[int] = Query(None, description="Filter by condition state ID"),
    state: Optional[str] = Query(
        None, description="Filter by condition state name (Available, Borrowed, etc.)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BookRead]:
    books, total = await crud_book.search(
        db=db,
        search=search,
        title=title,
        author=author,
        isbn=isbn,
        category_id=category_id,
        category_name=category,
        state_id=state_id,
        state_name=state,
        skip=offset,
        limit=limit,
    )

    items = []
    for b in books:
        b_read = BookRead.model_validate(b)
        b_read.is_borrowed = (
            (b.state.name.lower() in ("borrowed", "emprunté", "emprunte"))
            if b.state
            else False
        )
        items.append(b_read)

    pages = math.ceil(total / limit) if limit > 0 else 1
    return PaginatedResponse[BookRead](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        pages=pages,
    )


@router.get(
    "/{id}",
    response_model=BookRead,
    summary="Get book details by ID",
    description="Retrieve comprehensive details for a single book in the library catalog.",
)
async def read_book(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> BookRead:
    book = await crud_book.get_by_id(db, id=id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {id} was not found.",
        )
    b_read = BookRead.model_validate(book)
    b_read.is_borrowed = (
        (book.state.name.lower() in ("borrowed", "emprunté", "emprunte"))
        if book.state
        else False
    )
    return b_read


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new physical book",
    description="Adds a new book to the catalog. Validates ISBN integrity and Category existence. Defaults state to 'Available'.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def create_book(
    book_in: BookCreate,
    db: AsyncSession = Depends(get_db),
) -> BookRead:
    # 1. Verify Category exists
    category = await crud_category.get(db, id=book_in.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category ID {book_in.category_id} does not exist. Please specify a valid category.",
        )

    # 2. Verify ISBN uniqueness
    existing_isbn = await crud_book.get_by_isbn(db, isbn=book_in.isbn)
    if existing_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A book with ISBN '{book_in.isbn}' is already registered in the system (Book: '{existing_isbn.title}').",
        )

    # 3. Default state to 'Available' if not specified
    default_state_id = book_in.state_id
    if not default_state_id:
        avail_state = await crud_book_state.get_by_name(db, StateEnum.AVAILABLE.value)
        if not avail_state:
            avail_state = await crud_book_state.create(
                db, {"name": StateEnum.AVAILABLE.value}
            )
        default_state_id = avail_state.id

    book = await crud_book.create(db, obj_in=book_in, default_state_id=default_state_id)
    return BookRead.model_validate(book)


@router.put(
    "/{id}",
    response_model=BookRead,
    summary="Update book details",
    description="Update metadata, category, or condition state. Accessible by Administrator and Librarian.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def update_book(
    id: int,
    book_in: BookUpdate,
    db: AsyncSession = Depends(get_db),
) -> BookRead:
    book = await crud_book.get_by_id(db, id=id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {id} was not found.",
        )

    update_data = book_in.model_dump(exclude_unset=True)

    # If category changed, verify existence
    if "category_id" in update_data and update_data["category_id"] is not None:
        cat = await crud_category.get(db, id=update_data["category_id"])
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category ID {update_data['category_id']} does not exist.",
            )

    # If state changed, verify state existence
    if "state_id" in update_data and update_data["state_id"] is not None:
        state_obj = await crud_book_state.get(db, id=update_data["state_id"])
        if not state_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book state ID {update_data['state_id']} does not exist.",
            )

    # If ISBN changed, check uniqueness
    if "isbn" in update_data and update_data["isbn"]:
        existing = await crud_book.get_by_isbn(db, isbn=update_data["isbn"])
        if existing and existing.id != id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another book with ISBN '{update_data['isbn']}' already exists.",
            )

    updated_book = await crud_book.update(db, db_obj=book, obj_in=update_data)
    refreshed = await crud_book.get_by_id(db, id=updated_book.id)
    return BookRead.model_validate(refreshed)


@router.delete(
    "/{id}",
    response_model=Message,
    summary="Delete book from inventory",
    description="Deletes physical book. Raises error if book is currently on loan ('Borrowed').",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def delete_book(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> Message:
    book = await crud_book.get_by_id(db, id=id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {id} was not found.",
        )

    # Verify book is NOT currently on loan
    state_name = book.state.name.lower() if book.state else ""
    if state_name in ("borrowed", "emprunté", "emprunte"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete book '{book.title}' because it is currently on loan (Borrowed). Return it first.",
        )

    # Also verify no active unreturned loan transaction
    active_loan = await crud_transaction.get_active_by_book_id(db, book_id=id)
    if active_loan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete book '{book.title}' because it has an active loan transaction (ID #{active_loan.id}).",
        )

    await crud_book.remove(db, id=id)
    return Message(
        message=f"Book '{book.title}' (ISBN: {book.isbn}) was successfully removed from inventory."
    )
