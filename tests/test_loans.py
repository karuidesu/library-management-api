import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_borrow_and_return_cycle(
    client: AsyncClient, librarian_token: str, member_token: str
):
    # 1. Fetch current member ID
    me_res = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    member_id = me_res.json()["id"]

    # 2. Create an Available book
    book_res = await client.post(
        f"{settings.API_V1_STR}/books",
        json={
            "title": "Design Patterns: Elements of Reusable Object-Oriented Software",
            "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
            "isbn": "978-0-201-63361-0",
            "category_id": 1,
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert book_res.status_code == 201
    book_id = book_res.json()["id"]

    # 3. Librarian loans book to Member
    borrow_res = await client.post(
        f"{settings.API_V1_STR}/loans/borrow",
        json={"user_id": member_id, "book_id": book_id},
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert borrow_res.status_code == 201
    borrow_data = borrow_res.json()
    assert "successfully loaned" in borrow_data["message"]
    tx_id = borrow_data["transaction"]["id"]
    assert borrow_data["transaction"]["is_active"] is True

    # 4. Verify book status is now "Borrowed"
    check_book = await client.get(f"{settings.API_V1_STR}/books/{book_id}")
    assert check_book.json()["state"]["name"] == "Borrowed"

    # 5. Attempting to delete borrowed book must fail (400)
    del_attempt = await client.delete(
        f"{settings.API_V1_STR}/books/{book_id}",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert del_attempt.status_code == 400
    assert "currently on loan" in del_attempt.json()["detail"]

    # 6. Attempting to borrow the same book again must fail (400)
    reborrow = await client.post(
        f"{settings.API_V1_STR}/loans/borrow",
        json={"user_id": member_id, "book_id": book_id},
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert reborrow.status_code == 400
    assert "not available" in reborrow.json()["detail"]

    # 7. Check-in (Return book)
    return_res = await client.post(
        f"{settings.API_V1_STR}/loans/return",
        json={"transaction_id": tx_id},
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert return_res.status_code == 200
    assert "successfully returned" in return_res.json()["message"]
    assert return_res.json()["transaction"]["actual_return_date"] is not None

    # 8. Verify book status is back to "Available"
    after_return = await client.get(f"{settings.API_V1_STR}/books/{book_id}")
    assert after_return.json()["state"]["name"] == "Available"
