"""JSON API under /api: validate input → call a module's public API → map the result to HTTP."""

import secrets
from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict

from app.db import Db, open_db
from app.leave import LeaveRequest, list_my_requests, submit_request
from app.people import Person, get_person, list_people
from app.result import Err, ErrorCode

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
    working_days: int


class NewRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # no owner field: the owner is the session (AC-10)
    leave_type: Literal["Annual", "Unpaid"]
    start_date: date
    end_date: date


# The spec's refusal sentences (spec 0002, User experience); the UI shows them as they are.
REFUSALS = {
    ErrorCode.END_BEFORE_START: "The end date must be on or after the start date.",
    ErrorCode.NO_WORKING_DAYS: "This range has no working days.",
    ErrorCode.START_IN_PAST: "The start date cannot be in the past.",
    ErrorCode.SPANS_YEARS: "A request must start and end in the same calendar year.",
    ErrorCode.OVERLAP: "You already have a pending or approved request on these dates.",
}


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


def today() -> date:
    """The Clock: the server's local date (docs/architecture.md); tests override it."""
    return datetime.now(UTC).astimezone().date()


TodayDep = Annotated[date, Depends(today)]


def request_out(r: LeaveRequest) -> RequestOut:
    return RequestOut(
        id=r.id,
        leave_type=r.leave_type,
        start_date=r.start_date,
        end_date=r.end_date,
        status=r.status,
        working_days=r.working_days,
    )


@router.get("/people")
def people(db: DbDep) -> list[PersonOut]:
    return [PersonOut(id=p.id, full_name=p.full_name) for p in list_people(db)]


@router.post("/session", status_code=204)
def log_in(body: LoginIn, request: Request, db: DbDep) -> Response:
    live_sessions(request).pop(request.session.get("sid", ""), None)  # any login ends the old one
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
    return MyRequestsOut(requests=[request_out(r) for r in list_my_requests(db, actor)])


@router.post("/my/requests", status_code=201)
def submit(body: NewRequestIn, actor: ActorDep, db: DbDep, now: TodayDep) -> RequestOut:
    result = submit_request(db, actor, body.leave_type, body.start_date, body.end_date, now)
    if isinstance(result, Err):
        raise ApiError(409, result.code, REFUSALS[result.code])
    return request_out(result.value)
