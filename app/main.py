from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db import AsyncSessionLocal, Base, engine
from app.services.auth_service import auth_service

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agbale.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables, executes migrations/schema verification,
    and seeds default system roles, states, categories, and superuser.
    """
    logger.info("Starting Agbale API...")

    # 1. Ensure database tables are created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema verified.")

    # 2. Bootstrap standard roles, condition states, categories, and default admin
    async with AsyncSessionLocal() as session:
        try:
            await auth_service.bootstrap_initial_data(session)
        except Exception as exc:
            logger.error(f"Error during initial data bootstrap: {exc}", exc_info=True)

    yield

    # Teardown
    logger.info("Shutting down Agbale API and disposing connection pool...")
    await engine.dispose()
    logger.info("Connection pool closed.")


# Initialize FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Library Management System. \n"
        "Provides complete catalog, "
        "member management, role-based access control, "
        "loan circulation, and analytics capabilities."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.BACKEND_CORS_ORIGINS
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    tags=["Health"],
    summary="Service Root / API Information",
)
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "organization": settings.ORGANIZATION_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs",
        "redoc": f"{settings.API_V1_STR}/redoc",
        "openapi": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get(
    "/health",
    tags=["Health & Status"],
    summary="Service Health Check",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    # Verify DB connectivity
    db_status = "connected"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }
