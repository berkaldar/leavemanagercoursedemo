"""Leave requests and their rules (docs/domain.md, BR-1..BR-8)."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import uuid4

from app.db import Db, Row
from app.people import Person
from app.result import Err, ErrorCode, Ok, Result


@dataclass(frozen=True)
class LeaveRequest:
    id: str
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    status: str
    working_days: int


type Span = tuple[date, date]


def plant_shutdowns(db: Db) -> list[Span]:
    rows = db.fetch_all("SELECT start_date, end_date FROM plant_shutdowns")
    return [(date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])) for r in rows]


def working_days(start: date, end: date, shutdowns: list[Span]) -> int:
    """Monday–Friday in start … end (inclusive), minus Plant shutdown days (docs/domain.md)."""
    days = (start + timedelta(n) for n in range((end - start).days + 1))
    return sum(1 for d in days if d.weekday() < 5 and not any(s <= d <= e for s, e in shutdowns))


def list_my_requests(db: Db, actor: Person) -> list[LeaveRequest]:
    """Only the actor's own requests (Authorization: an Employee sees their own)."""
    rows = db.fetch_all(
        "SELECT * FROM leave_requests WHERE employee_id = ? ORDER BY start_date", (actor.id,)
    )
    shutdowns = plant_shutdowns(db)
    return [_request(r, shutdowns) for r in rows]


def _request(row: Row, shutdowns: list[Span]) -> LeaveRequest:
    start, end = date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"])
    return LeaveRequest(
        id=row["id"],
        employee_id=row["employee_id"],
        leave_type=row["leave_type"],
        start_date=start,
        end_date=end,
        status=row["status"],
        working_days=working_days(start, end, shutdowns),
    )


def submit_request(
    db: Db, actor: Person, leave_type: str, start: date, end: date, today: date
) -> Result[LeaveRequest]:
    """The actor's own new Pending request; checks run in spec 0002 R-5 order (BR-1/3/6)."""
    shutdowns = plant_shutdowns(db)
    if end < start:
        return Err(ErrorCode.END_BEFORE_START)
    if working_days(start, end, shutdowns) == 0:
        return Err(ErrorCode.NO_WORKING_DAYS)
    if start < today:
        return Err(ErrorCode.START_IN_PAST)
    if start.year != end.year:
        return Err(ErrorCode.SPANS_YEARS)
    row: Row = {
        "id": str(uuid4()),
        "employee_id": actor.id,
        "leave_type": leave_type,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "status": "Pending",
    }
    # One statement: the overlap check and the save cannot interleave with another submit (BR-3).
    inserted = db.execute(
        """INSERT INTO leave_requests
               (id, employee_id, leave_type, start_date, end_date, status, created_at)
           SELECT ?, ?, ?, ?, ?, ?, ?
           WHERE NOT EXISTS (
               SELECT 1 FROM leave_requests
               WHERE employee_id = ? AND status IN ('Pending', 'Approved')
                 AND start_date <= ? AND end_date >= ?)""",
        (*row.values(), today.isoformat(), actor.id, row["end_date"], row["start_date"]),
    )
    return Ok(_request(row, shutdowns)) if inserted else Err(ErrorCode.OVERLAP)
