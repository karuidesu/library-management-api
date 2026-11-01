import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_get_system_info_public(client: AsyncClient):
    """
    Test that the public system information endpoint returns
    the organization and application name without authentication.
    """
    response = await client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()

    assert data["app_name"] == settings.PROJECT_NAME
    assert data["organization_name"] == settings.ORGANIZATION_NAME
    assert data["version"] == "1.0.0"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["debug"] == settings.DEBUG


@pytest.mark.asyncio
async def test_root_endpoint_includes_organization(client: AsyncClient):
    """
    Test that the service root endpoint '/' exposes the organization branding.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == settings.PROJECT_NAME
    assert data["organization"] == settings.ORGANIZATION_NAME
    assert data["status"] == "online"
