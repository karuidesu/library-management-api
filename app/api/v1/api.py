from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    books,
    categories,
    loans,
    states,
    system,
    users,
)

api_router = APIRouter()

api_router.include_router(system.router, prefix="/system", tags=["Settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(books.router, prefix="/books", tags=["Books"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(states.router, prefix="/states", tags=["Book States"])
api_router.include_router(loans.router, prefix="/loans", tags=["Inventory"])
api_router.include_router(
    analytics.router, prefix="/analytics", tags=["Statistics"]
)
