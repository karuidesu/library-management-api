from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import require_roles
from app.crud.crud_book_state import crud_book_state
from app.models.book import Book
from app.schemas.book_state import BookStateCreate, BookStateRead, BookStateUpdate
from app.schemas.common import Message

router = APIRouter()


@router.get(
    "",
    response_model=List[BookStateRead],
    summary="List all book condition states",
    description="Retrieve all book condition states (Available, Borrowed, Damaged, Lost). Accessible by all users.",
)
async def read_states(
    db: AsyncSession = Depends(get_db),
) -> List[BookStateRead]:
    states = await crud_book_state.get_multi(db, skip=0, limit=100)
    return [BookStateRead.model_validate(s) for s in states]


@router.get(
    "/{id}",
    response_model=BookStateRead,
    summary="Get state by ID",
    description="Retrieve specific condition state.",
)
async def read_state(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> BookStateRead:
    state = await crud_book_state.get(db, id=id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BookState with ID {id} was not found.",
        )
    return BookStateRead.model_validate(state)


@router.post(
    "",
    response_model=BookStateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create book condition state",
    description="Admin and Librarian can create new book condition states.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def create_state(
    state_in: BookStateCreate,
    db: AsyncSession = Depends(get_db),
) -> BookStateRead:
    existing = await crud_book_state.get_by_name(db, name=state_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BookState '{state_in.name}' already exists.",
        )
    state = await crud_book_state.create(db, obj_in=state_in)
    return BookStateRead.model_validate(state)


@router.put(
    "/{id}",
    response_model=BookStateRead,
    summary="Update condition state",
    description="Admin and Librarian can update book state names.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def update_state(
    id: int,
    state_in: BookStateUpdate,
    db: AsyncSession = Depends(get_db),
) -> BookStateRead:
    state = await crud_book_state.get(db, id=id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BookState with ID {id} was not found.",
        )
    if state_in.name:
        existing = await crud_book_state.get_by_name(db, name=state_in.name)
        if existing and existing.id != id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BookState '{state_in.name}' already exists.",
            )
    updated = await crud_book_state.update(db, db_obj=state, obj_in=state_in)
    return BookStateRead.model_validate(updated)


@router.delete(
    "/{id}",
    response_model=Message,
    summary="Delete condition state",
    description="Admin and Librarian can delete condition states not currently referenced by any books.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def delete_state(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> Message:
    state = await crud_book_state.get(db, id=id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BookState with ID {id} was not found.",
        )
    # Check if books reference this state
    stmt = select(func.count(Book.id)).where(Book.state_id == id)
    count_res = await db.execute(stmt)
    count = count_res.scalar() or 0
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete state '{state.name}' because {count} book(s) are assigned to it.",
        )
    await crud_book_state.remove(db, id=id)
    return Message(message=f"BookState '{state.name}' was successfully deleted.")
