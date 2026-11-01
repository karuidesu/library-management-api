import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_create_book_success(client: AsyncClient, librarian_token: str):
    # Valid ISBN-13: 978-0-306-40615-7
    response = await client.post(
        f"{settings.API_V1_STR}/books",
        json={
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "author": "Robert C. Martin",
            "isbn": "978-0-306-40615-7",
            "category_id": 1,
            "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
            "publication_year": 2008,
            "copies": 5,
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Code: A Handbook of Agile Software Craftsmanship"
    assert data["state"]["name"] == "Available"
    assert data["category"]["id"] == 1


@pytest.mark.asyncio
async def test_create_book_invalid_isbn_checksum(
    client: AsyncClient, librarian_token: str
):
    # Tampered checksum at the end
    response = await client.post(
        f"{settings.API_V1_STR}/books",
        json={
            "title": "Invalid Book",
            "author": "Tester",
            "isbn": "978-0-306-40615-9",  # Invalid checksum!
            "category_id": 1,
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_book_invalid_category(client: AsyncClient, librarian_token: str):
    # Valid ISBN-10: 0-306-40615-2
    response = await client.post(
        f"{settings.API_V1_STR}/books",
        json={
            "title": "Orphan Book",
            "author": "Unknown",
            "isbn": "0-306-40615-2",
            "category_id": 99999,  # Non-existent category
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_books_pagination(client: AsyncClient, librarian_token: str):
    # Create a book to search
    await client.post(
        f"{settings.API_V1_STR}/books",
        json={
            "title": "The Pragmatic Programmer",
            "author": "David Thomas, Andrew Hunt",
            "isbn": "978-0-201-61622-4",
            "category_id": 1,
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )

    # Search by author
    search_res = await client.get(
        f"{settings.API_V1_STR}/books?author=Thomas",
    )
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total"] >= 1
    assert any("Pragmatic" in b["title"] for b in data["items"])
