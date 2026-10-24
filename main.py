"""
Main entrypoint exposing the FastAPI application instance.
Allows running via `uvicorn main:app --reload` or `python main.py`.
"""

import uvicorn
from app.core.config import settings
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.BINDING_HOST,
        port=settings.BINDING_PORT,
        reload=settings.DEBUG,
    )
