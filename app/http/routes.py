"""JSON API under /api: validate input → call a module's public API → map the result to HTTP."""

import secrets
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict

from app.db import Db, open_db
from app.leave import list_my_requests
from app.people import Person, get_person, list_people
from app.result import Err

router = APIRouter(prefix="/api")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message


class PersonOut(BaseModel):
    id: str
    full_name: str


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    person_id: str


class RequestOut(BaseModel):
    id: str
    leave_type: str
    start_date: date
    end_date: date
    status: str


class MyRequestsOut(BaseModel):
    requests: list[RequestOut]


def get_db(request: Request) -> Iterator[Db]:
    db = open_db(request.app.state.db_uri)  # one connection per request (Known traps)
    try:
        yield db
    finally:
        db.close()


DbDep = Annotated[Db, Depends(get_db)]


def live_sessions(request: Request) -> dict[str, str]:
    # shortcut: live session ids live in process memory (single process, lost on restart);
    # move them to the database when the app runs as more than one process.
    sessions: dict[str, str] = request.app.state.sessions
    return sessions


def current_person(request: Request, db: DbDep) -> Person:
    """Default-deny: every route that depends on this refuses a request without a live session."""
    person_id = live_sessions(request).get(request.session.get("sid", ""))
    result = get_person(db, person_id) if person_id else None
    if result is None or isinstance(result, Err):
        request.session.clear()
        raise ApiError(401, "NOT_LOGGED_IN", "Log in first.")
    return result.value


ActorDep = Annotated[Person, Depends(current_person)]


@router.get("/people")
def people(db: DbDep) -> list[PersonOut]:
    return [PersonOut(id=p.id, full_name=p.full_name) for p in list_people(db)]


@router.post("/session", status_code=204)
def log_in(body: LoginIn, request: Request, db: DbDep) -> Response:
    request.session.clear()
    if isinstance(get_person(db, body.person_id), Err):
        raise ApiError(404, "NOT_FOUND", "No such person.")
    sid = secrets.token_urlsafe(32)  # a fresh id on every login: no session fixation
    live_sessions(request)[sid] = body.person_id
    request.session["sid"] = sid
    return Response(status_code=204)


@router.delete("/session", status_code=204)
def log_out(request: Request) -> Response:
    live_sessions(request).pop(request.session.get("sid", ""), None)
    request.session.clear()
    return Response(status_code=204)


@router.get("/me")
def me(actor: ActorDep) -> PersonOut:
    return PersonOut(id=actor.id, full_name=actor.full_name)


@router.get("/my/requests")
def my_requests(actor: ActorDep, db: DbDep) -> MyRequestsOut:
    return MyRequestsOut(
        requests=[
            RequestOut(
                id=r.id,
                leave_type=r.leave_type,
                start_date=r.start_date,
                end_date=r.end_date,
                status=r.status,
            )
            for r in list_my_requests(db, actor)
        ]
    )
