from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db import ALI_ID, ELIF_ID, open_db
from app.http import today
from app.main import create_app
from tests.conftest import memory_db_uri

WEEK = {"leave_type": "Annual", "start_date": "2026-11-16", "end_date": "2026-11-20"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(memory_db_uri(), session_secret="test-secret")
    app.dependency_overrides[today] = lambda: date(2026, 11, 14)
    yield TestClient(app)
    app.state.anchor.close()


def login(client: TestClient, person_id: str = ALI_ID) -> None:
    assert client.post("/api/session", json={"person_id": person_id}).status_code == 204


def stored_rows(client: TestClient) -> list[dict[str, Any]]:
    db = open_db(client.app.state.db_uri)  # type: ignore[attr-defined]
    try:
        return db.fetch_all("SELECT employee_id, start_date FROM leave_requests")
    finally:
        db.close()


def test_submit_then_listed(client: TestClient) -> None:
    login(client)
    response = client.post("/api/my/requests", json=WEEK)
    assert response.status_code == 201
    row = {**WEEK, "status": "Pending", "working_days": 5}
    assert {k: response.json()[k] for k in row} == row
    [listed] = client.get("/api/my/requests").json()["requests"]
    assert {k: listed[k] for k in row} == row


@pytest.mark.parametrize(
    ("body", "code", "message"),
    [
        (
            {**WEEK, "end_date": "2026-11-15"},
            "END_BEFORE_START",
            "The end date must be on or after the start date.",
        ),
        (
            {**WEEK, "start_date": "2026-11-21", "end_date": "2026-11-22"},
            "NO_WORKING_DAYS",
            "This range has no working days.",
        ),
        (
            {**WEEK, "start_date": "2026-11-13"},
            "START_IN_PAST",
            "The start date cannot be in the past.",
        ),
        (
            {**WEEK, "start_date": "2026-12-21", "end_date": "2027-01-04"},
            "SPANS_YEARS",
            "A request must start and end in the same calendar year.",
        ),
    ],
)
def test_refusal_saves_nothing(
    client: TestClient, body: dict[str, str], code: str, message: str
) -> None:
    login(client)
    response = client.post("/api/my/requests", json=body)
    assert (response.status_code, response.json()) == (409, {"error": code, "message": message})
    assert stored_rows(client) == []


def test_overlap_refused_with_its_sentence(client: TestClient) -> None:
    login(client)
    assert client.post("/api/my/requests", json=WEEK).status_code == 201
    response = client.post("/api/my/requests", json={**WEEK, "start_date": "2026-11-20"})
    assert response.status_code == 409
    assert response.json() == {
        "error": "OVERLAP",
        "message": "You already have a pending or approved request on these dates.",
    }
    assert len(stored_rows(client)) == 1


@pytest.mark.parametrize(
    "body",
    [
        {k: v for k, v in WEEK.items() if k != "leave_type"},
        {k: v for k, v in WEEK.items() if k != "start_date"},
        {k: v for k, v in WEEK.items() if k != "end_date"},
        {**WEEK, "leave_type": "Sick"},
        {**WEEK, "start_date": "2026-13-01"},
        {**WEEK, "end_date": "not a date"},
    ],
)
def test_invalid_input_refused(client: TestClient, body: dict[str, str]) -> None:
    login(client)
    response = client.post("/api/my/requests", json=body)
    assert (response.status_code, response.json()["error"]) == (422, "INVALID_INPUT")
    assert stored_rows(client) == []


def test_owner_is_always_the_actor(client: TestClient) -> None:
    login(client)
    forged = client.post("/api/my/requests", json={**WEEK, "employee_id": ELIF_ID})
    assert forged.status_code == 422
    assert stored_rows(client) == []
    assert client.post("/api/my/requests", json=WEEK).status_code == 201
    assert stored_rows(client) == [{"employee_id": ALI_ID, "start_date": "2026-11-16"}]


def test_submit_without_login_refused(client: TestClient) -> None:
    response = client.post("/api/my/requests", json=WEEK)
    assert (response.status_code, response.json()["error"]) == (401, "NOT_LOGGED_IN")
    assert stored_rows(client) == []
