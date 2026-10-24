"""
Runner script for Agbale.
Usage: python run.py
"""

import sys
from pathlib import Path
import uvicorn

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings  # noqa: E402

if __name__ == "__main__":
    print(
        f"Starting {settings.PROJECT_NAME} on http://{settings.BINDING_HOST}:{settings.BINDING_PORT}"
    )
    print(
        f"Interactive API Documentation: http://127.0.0.1:{settings.BINDING_PORT}{settings.API_V1_STR}/docs"
    )
    uvicorn.run(
        "app.main:app",
        host=settings.BINDING_HOST,
        port=settings.BINDING_PORT,
        reload=settings.DEBUG,
    )
