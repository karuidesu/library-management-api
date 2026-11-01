import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_login_success_form(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == settings.FIRST_SUPERUSER_EMAIL
    assert data["user"]["role"]["label"] == "Administrator"


@pytest.mark.asyncio
async def test_login_success_json(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login-json",
        json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == settings.FIRST_SUPERUSER_EMAIL


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login-json",
        json={
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_member_success(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "name": "Jean Dupont",
            "email": "jean.dupont@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jean Dupont"
    assert data["email"] == "jean.dupont@example.com"
    assert data["role"]["label"] == "Member"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # First registration
    await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "name": "Marie Curie",
            "email": "marie.curie@example.com",
            "password": "Password123!",
        },
    )
    # Second duplicate registration
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "name": "Marie Duplicate",
            "email": "marie.curie@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
