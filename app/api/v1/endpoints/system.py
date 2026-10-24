from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter()


class SystemInfoResponse(BaseModel):
    app_name: str = Field(..., description="Application name")
    organization_name: str = Field(..., description="Organization or institution name")
    version: str = Field("1.0.0", description="API version")
    environment: str = Field(
        ..., description="Current environment (development, production)"
    )
    debug: bool = Field(..., description="Debug mode indicator")


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="Get public system and organization branding",
    description=(
        "Public endpoint returning application and institution/organization "
        "branding for frontend headers, login view, and footers."
    ),
)
async def get_system_info() -> SystemInfoResponse:
    return SystemInfoResponse(
        app_name=settings.PROJECT_NAME,
        organization_name=settings.ORGANIZATION_NAME,
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
