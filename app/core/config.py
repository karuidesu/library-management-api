from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables and .env file.
    Follows SOLID principles for centralized configuration management.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # API Configuration
    PROJECT_NAME: str = "Agbale"
    ORGANIZATION_NAME: str = "Bibliothèque Publique Agbale"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    BINDING_HOST: str = "0.0.0.0"
    BINDING_PORT: int = 8000

    # Security & JWT
    SECRET_KEY: str = "agbale-super-secret-development-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./agbale.db"

    # Default Seed Admin
    FIRST_SUPERUSER_NAME: str = "System Administrator"
    FIRST_SUPERUSER_EMAIL: str = "admin@agbale.org"
    FIRST_SUPERUSER_PASSWORD: str = "AdminPassword123!"

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
