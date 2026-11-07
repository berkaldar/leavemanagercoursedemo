"""create_app(): wires the API, session, security headers and the static frontend."""

import os
import secrets
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db import migrate, open_db, seed
from app.http import ApiError, router

WEB = Path(__file__).resolve().parent.parent / "web"


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)


def create_app(db_uri: str, session_secret: str) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db_uri = db_uri
    app.state.sessions = {}
    # Kept open for the app's lifetime: a shared memory database lives only while a connection does.
    app.state.anchor = open_db(db_uri)
    migrate(app.state.anchor)
    seed(app.state.anchor)

    # max_age=None: a browser-session cookie, gone when the browser closes (spec 0001, R-3).
    app.add_middleware(SessionMiddleware, secret_key=session_secret, max_age=None, same_site="lax")

    @app.middleware("http")
    async def content_security_policy(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error(422, "INVALID_INPUT", "The request is not valid.")

    @app.exception_handler(Exception)
    async def internal(request: Request, exc: Exception) -> JSONResponse:
        return error(500, "INTERNAL", "Something went wrong.")

    app.include_router(router)
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app


def create_app_from_env() -> FastAPI:
    """Local run: `scripts/py -m uvicorn --factory app.main:create_app_from_env`."""
    secret = os.environ.get("SESSION_SECRET") or secrets.token_urlsafe(32)  # unset: per process
    return create_app(os.environ.get("LEAVE_DB", "file:leave.db"), secret)
