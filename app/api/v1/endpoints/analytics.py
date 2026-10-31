from typing import List, Union
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import require_roles
from app.schemas.analytics import CategoryBorrowStats, DashboardStats, ReportItem
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Dashboard KPIs & circulation overview",
    description=(
        "High-level library aggregates: Total Books, Active Members, "
        "Borrowed Books, Overdue Loans, and Recent Circulation Activity. "
        "Accessible by Administrator and Librarian."
    ),
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    return await analytics_service.get_dashboard_stats(db=db)


@router.get(
    "/categories",
    response_model=List[CategoryBorrowStats],
    summary="Categorical borrowing frequency statistics",
    description=(
        "Returns genre/subject categories ranked by historical circulation frequency, "
        "with active loan counts and total inventory. Accessible by Administrator and Librarian."
    ),
    dependencies=[Depends(require_roles(["Administrator", "Librarian"]))],
)
async def get_category_stats(
    db: AsyncSession = Depends(get_db),
) -> List[CategoryBorrowStats]:
    return await analytics_service.get_category_borrow_stats(db=db)


@router.get(
    "/reports",
    response_model=Union[List[ReportItem], str],
    summary="Generate system historical audit reports",
    description=(
        "Retrieves historical circulation audit logs. "
        "Supports format='json' (default) or format='csv' for direct spreadsheet download. "
        "Restricted to Administrator only."
    ),
    dependencies=[Depends(require_roles(["Administrator"]))],
)
async def get_reports(
    format: str = Query(
        "json", pattern="^(json|csv)$", description="Output format: 'json' or 'csv'"
    ),
    limit: int = Query(1000, ge=1, le=5000, description="Max audit entries to include"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    reports = await analytics_service.get_audit_reports(db=db, skip=0, limit=limit)

    if format.lower() == "csv":
        csv_content = analytics_service.export_reports_to_csv(reports)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=library_audit_report.csv"
            },
        )

    # Return standard JSON
    return [r.model_dump() for r in reports]  # type: ignore
