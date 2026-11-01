import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_get_user_me(client: AsyncClient, member_token: str):
    response = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alex.mercer@gmail.com"
    assert data["role"]["label"] == "Member"
    assert "active_loans_count" in data


@pytest.mark.asyncio
async def test_list_users_rbac_enforcement(
    client: AsyncClient, member_token: str, admin_token: str
):
    # Member should be forbidden (403)
    res_member = await client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res_member.status_code == 403

    # Admin should succeed (200)
    res_admin = await client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_update_user_permissions(
    client: AsyncClient, member_token: str, admin_token: str
):
    # Get current member profile
    me_res = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    member_id = me_res.json()["id"]

    # Member updates own name
    update_res = await client.put(
        f"{settings.API_V1_STR}/users/{member_id}",
        json={"name": "Alex Mercer Updated"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Alex Mercer Updated"

    # Member attempts to promote themself to Admin (role_id=1) -> 403
    forbidden_res = await client.put(
        f"{settings.API_V1_STR}/users/{member_id}",
        json={"role_id": 1},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert forbidden_res.status_code == 403
    assert "Only Administrators can change user roles" in forbidden_res.json()["detail"]


@pytest.mark.asyncio
async def test_delete_user_admin_only(
    client: AsyncClient, member_token: str, admin_token: str
):
    # Create temporary user to delete
    reg_res = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "name": "Temp User",
            "email": "temp.delete@example.com",
            "password": "Password123!",
        },
    )
    temp_id = reg_res.json()["id"]

    # Member tries to delete -> 403
    del_member = await client.delete(
        f"{settings.API_V1_STR}/users/{temp_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert del_member.status_code == 403

    # Admin deletes -> 200
    del_admin = await client.delete(
        f"{settings.API_V1_STR}/users/{temp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_admin.status_code == 200
    assert "successfully deleted" in del_admin.json()["message"]
