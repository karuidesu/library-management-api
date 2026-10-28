from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import require_roles
from app.crud.crud_category import crud_category
from app.models.book import Book
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import Message

router = APIRouter()


@router.get(
    "",
    response_model=List[CategoryRead],
    summary="List all categories",
    description="Retrieve all book categories with real-time catalog item counts. Accessible by all members.",
)
async def read_categories(
    db: AsyncSession = Depends(get_db),
) -> List[CategoryRead]:
    categories, _ = await crud_category.get_multi_with_counts(db=db, skip=0, limit=200)

    result = []
    for cat in categories:
        stmt = select(func.count(Book.id)).where(Book.category_id == cat.id)
        count_res = await db.execute(stmt)
        count = count_res.scalar() or 0
        c_read = CategoryRead(
            id=cat.id, name=cat.name, created_at=cat.created_at, books_count=count
        )
        result.append(c_read)
    return result


@router.get(
    "/{id}",
    response_model=CategoryRead,
    summary="Get category details",
    description="Retrieve a single category by ID.",
)
async def read_category(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    cat = await crud_category.get(db=db, id=id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} was not found.",
        )
    stmt = select(func.count(Book.id)).where(Book.category_id == cat.id)
    count_res = await db.execute(stmt)
    count = count_res.scalar() or 0
    return CategoryRead(
        id=cat.id, name=cat.name, created_at=cat.created_at, books_count=count
    )


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Admin and Librarian can create new genre/subject categories.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    existing = await crud_category.get_by_name(db, name=category_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_in.name}' already exists.",
        )
    cat = await crud_category.create(db, obj_in=category_in)
    return CategoryRead.model_validate(cat)


@router.put(
    "/{id}",
    response_model=CategoryRead,
    summary="Update category",
    description="Admin and Librarian can update category details.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def update_category(
    id: int,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    cat = await crud_category.get(db, id=id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} was not found.",
        )
    if category_in.name:
        existing = await crud_category.get_by_name(db, name=category_in.name)
        if existing and existing.id != id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_in.name}' already exists.",
            )
    updated = await crud_category.update(db, db_obj=cat, obj_in=category_in)
    return CategoryRead.model_validate(updated)


@router.delete(
    "/{id}",
    response_model=Message,
    summary="Delete category",
    description="Admin and Librarian can delete categories that have no books assigned.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def delete_category(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> Message:
    cat = await crud_category.get(db, id=id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {id} was not found.",
        )
    # Check if books belong to this category
    stmt = select(func.count(Book.id)).where(Book.category_id == id)
    count_res = await db.execute(stmt)
    count = count_res.scalar() or 0
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{cat.name}' because {count} book(s) are assigned to it.",
        )
    await crud_category.remove(db, id=id)
    return Message(message=f"Category '{cat.name}' was successfully deleted.")
