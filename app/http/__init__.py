"""HTTP boundary: FastAPI routes and session (docs/architecture.md)."""

from app.http.routes import ApiError, router

__all__ = ["ApiError", "router"]
