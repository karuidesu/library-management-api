from typing import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import Base, get_db
from app.core.security import create_access_token
from app.crud.crud_book_state import crud_book_state
from app.crud.crud_category import crud_category
from app.crud.crud_role import crud_role
from app.crud.crud_user import crud_user
from app.main import app
from app.models.role import RoleEnum

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        # Seed standard initial data
        await crud_role.ensure_roles(session)
        await crud_book_state.ensure_states(session)
        await crud_category.ensure_default_categories(session)

        # Seed test admin
        admin_role = await crud_role.get_by_label(session, RoleEnum.ADMINISTRATOR.value)
        admin = await crud_user.get_by_email(session, settings.FIRST_SUPERUSER_EMAIL)
        if not admin and admin_role:
            await crud_user.create(
                session,
                obj_in={
                    "name": settings.FIRST_SUPERUSER_NAME,
                    "email": settings.FIRST_SUPERUSER_EMAIL,
                    "password": settings.FIRST_SUPERUSER_PASSWORD,
                    "is_active": True,
                    "role_id": admin_role.id,
                },
                role_id=admin_role.id,
            )

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_token(db_session: AsyncSession) -> str:
    admin = await crud_user.get_by_email(db_session, settings.FIRST_SUPERUSER_EMAIL)
    assert admin is not None
    token = create_access_token(
        subject=admin.id,
        extra_claims={"role": RoleEnum.ADMINISTRATOR.value, "email": admin.email},
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def librarian_token(db_session: AsyncSession) -> str:
    lib_role = await crud_role.get_by_label(db_session, RoleEnum.LIBRARIAN.value)
    assert lib_role is not None
    user = await crud_user.create(
        db_session,
        obj_in={
            "name": "Sarah Connor",
            "email": "sarah.librarian@agbale.org",
            "password": "Password123!",
            "is_active": True,
            "role_id": lib_role.id,
        },
        role_id=lib_role.id,
    )
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": RoleEnum.LIBRARIAN.value, "email": user.email},
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def member_token(db_session: AsyncSession) -> str:
    member_role = await crud_role.get_by_label(db_session, RoleEnum.MEMBER.value)
    assert member_role is not None
    user = await crud_user.create(
        db_session,
        obj_in={
            "name": "Alex Mercer",
            "email": "alex.mercer@gmail.com",
            "password": "Password123!",
            "is_active": True,
            "role_id": member_role.id,
        },
        role_id=member_role.id,
    )
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": RoleEnum.MEMBER.value, "email": user.email},
    )
    return token
