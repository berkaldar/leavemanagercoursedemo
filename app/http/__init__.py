"""HTTP boundary: FastAPI routes and session (docs/architecture.md)."""

from app.http.routes import ApiError, router, today

__all__ = ["ApiError", "router", "today"]
