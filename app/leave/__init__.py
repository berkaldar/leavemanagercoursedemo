"""Leave requests and their rules (docs/domain.md, BR-1..BR-6)."""

from dataclasses import dataclass
from datetime import date

from app.db import Db
from app.people import Person


@dataclass(frozen=True)
class LeaveRequest:
    id: str
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    status: str


def list_my_requests(db: Db, actor: Person) -> list[LeaveRequest]:
    """Only the actor's own requests (Authorization: an Employee sees their own)."""
    rows = db.fetch_all(
        "SELECT * FROM leave_requests WHERE employee_id = ? ORDER BY start_date", (actor.id,)
    )
    return [
        LeaveRequest(
            id=r["id"],
            employee_id=r["employee_id"],
            leave_type=r["leave_type"],
            start_date=date.fromisoformat(r["start_date"]),
            end_date=date.fromisoformat(r["end_date"]),
            status=r["status"],
        )
        for r in rows
    ]
