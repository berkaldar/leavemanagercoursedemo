from datetime import date

from app.db import ALI_ID, ELIF_ID, Db
from app.leave import list_my_requests
from app.people import Person


def person(person_id: str) -> Person:
    return Person(id=person_id, full_name="x", manager_id=None)


def test_fresh_person_has_no_requests(db: Db) -> None:
    assert list_my_requests(db, person(ALI_ID)) == []


def test_only_own_requests_returned(db: Db) -> None:
    db.execute(
        "INSERT INTO leave_requests VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "r-1",
            ELIF_ID,
            "Annual",
            "2026-03-02",
            "2026-03-06",
            "Pending",
            "2026-02-01T09:00:00+00:00",
        ),
    )
    assert list_my_requests(db, person(ALI_ID)) == []
    [own] = list_my_requests(db, person(ELIF_ID))
    assert (own.employee_id, own.start_date, own.end_date) == (
        ELIF_ID,
        date(2026, 3, 2),
        date(2026, 3, 6),
    )
