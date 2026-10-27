import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.crud.crud_transaction import crud_transaction
from app.crud.crud_user import crud_user
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.common import Message, PaginatedResponse
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
    description="Returns authenticated user details, assigned role, and current active loans count.",
)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await crud_user.get_by_id(db, id=current_user.id)
    active_count = await crud_transaction.count_active_user_loans(
        db, user_id=current_user.id
    )
    user_res = UserRead.model_validate(user)
    user_res.active_loans_count = active_count
    return user_res


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="List and search users",
    description="Search and filter users by query, name, or role. Accessible by Administrator and Librarian.",
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def read_users(
    query: Optional[str] = Query(None, description="Search query across name or email"),
    name: Optional[str] = Query(None, description="Filter specifically by name"),
    role: Optional[str] = Query(
        None, description="Filter by role label (Administrator, Librarian, Member)"
    ),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserRead]:
    users, total = await crud_user.search(
        db=db,
        query=query,
        name=name,
        role_id=role_id,
        role_label=role,
        is_active=is_active,
        skip=offset,
        limit=limit,
    )

    items = []
    for u in users:
        u_read = UserRead.model_validate(u)
        u_read.active_loans_count = await crud_transaction.count_active_user_loans(
            db, user_id=u.id
        )
        items.append(u_read)

    pages = math.ceil(total / limit) if limit > 0 else 1
    return PaginatedResponse[UserRead](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        pages=pages,
    )


@router.get(
    "/{id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Retrieve user profile by ID. Accessible by Administrator, Librarian, or the user themself.",
)
async def read_user_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    caller_role = current_user.role.label if current_user.role else ""
    is_privileged = caller_role in [
        RoleEnum.ADMINISTRATOR.value,
        RoleEnum.LIBRARIAN.value,
    ]

    if not is_privileged and current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view other users' profiles.",
        )

    user = await crud_user.get_by_id(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {id} was not found.",
        )

    user_read = UserRead.model_validate(user)
    user_read.active_loans_count = await crud_transaction.count_active_user_loans(
        db, user_id=id
    )
    return user_read


@router.put(
    "/{id}",
    response_model=UserRead,
    summary="Update user profile or role",
    description="Updates user profile. Only Administrators can change role_id or active status.",
)
async def update_user(
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    target_user = await crud_user.get_by_id(db, id=id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {id} was not found.",
        )

    caller_role = current_user.role.label if current_user.role else ""
    is_admin = (
        caller_role == RoleEnum.ADMINISTRATOR.value or caller_role == "Administrator"
    )
    is_librarian = caller_role == RoleEnum.LIBRARIAN.value or caller_role == "Librarian"
    is_owner = current_user.id == id

    if not (is_admin or is_librarian or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this account.",
        )

    update_dict = user_in.model_dump(exclude_unset=True)

    # Restrict privileged field modifications to Administrator only
    if not is_admin:
        if "role_id" in update_dict and update_dict["role_id"] != target_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Administrators can change user roles.",
            )
        if (
            "is_active" in update_dict
            and update_dict["is_active"] != target_user.is_active
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Administrators can activate or deactivate accounts.",
            )

    # Check email uniqueness if email is changed
    if "email" in update_dict and update_dict["email"] != target_user.email:
        existing = await crud_user.get_by_email(db, email=update_dict["email"])
        if existing and existing.id != id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already in use by another account.",
            )

    updated_user = await crud_user.update_user(
        db, db_obj=target_user, obj_in=update_dict
    )
    return UserRead.model_validate(updated_user)


@router.delete(
    "/{id}",
    response_model=Message,
    summary="Delete user account",
    description="Removes inactive or revoked accounts. Enforces Administrator privilege.",
    dependencies=[Depends(require_roles(["Administrator"]))],
)
async def delete_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Message:
    if current_user.id == id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own active account.",
        )

    target_user = await crud_user.get_by_id(db, id=id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {id} was not found.",
        )

    # Verify no active unreturned loans exist for this member
    active_loans = await crud_transaction.count_active_user_loans(db, user_id=id)
    if active_loans > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete user '{target_user.name}'. "
                f"They currently hold {active_loans} active borrowed book(s). Return all books first."
            ),
        )

    await crud_user.remove(db, id=id)
    return Message(
        message=f"User '{target_user.name}' ({target_user.email}) successfully deleted."
    )
