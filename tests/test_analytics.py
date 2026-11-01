import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_dashboard_analytics_kpi(client: AsyncClient, librarian_token: str):
    response = await client.get(
        f"{settings.API_V1_STR}/analytics/dashboard",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_books" in data
    assert "active_members" in data
    assert "borrowed_books" in data
    assert "overdue_loans" in data
    assert "total_categories" in data
    assert "recent_activities" in data


@pytest.mark.asyncio
async def test_category_borrowing_frequency(client: AsyncClient, librarian_token: str):
    response = await client.get(
        f"{settings.API_V1_STR}/analytics/categories",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert response.status_code == 200
    stats = response.json()
    assert isinstance(stats, list)
    assert len(stats) >= 1
    assert "category_name" in stats[0]
    assert "borrow_count" in stats[0]


@pytest.mark.asyncio
async def test_audit_reports_json_and_csv(
    client: AsyncClient, admin_token: str, member_token: str
):
    # Non-admin access should be forbidden (403)
    forbidden = await client.get(
        f"{settings.API_V1_STR}/analytics/reports",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert forbidden.status_code == 403

    # Admin JSON format
    json_res = await client.get(
        f"{settings.API_V1_STR}/analytics/reports?format=json",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert json_res.status_code == 200
    assert isinstance(json_res.json(), list)

    # Admin CSV download format
    csv_res = await client.get(
        f"{settings.API_V1_STR}/analytics/reports?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Transaction ID,Status,Borrow Date (UTC)" in csv_res.text
