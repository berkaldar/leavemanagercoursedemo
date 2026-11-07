"""Employees and the Manager relation (docs/domain.md)."""

from dataclasses import dataclass

from app.db import Db, Row
from app.result import Err, ErrorCode, Ok, Result


@dataclass(frozen=True)
class Person:
    id: str
    full_name: str
    manager_id: str | None


def _person(row: Row) -> Person:
    return Person(id=row["id"], full_name=row["full_name"], manager_id=row["manager_id"])


def list_people(db: Db) -> list[Person]:
    # shortcut: SQLite's binary collation sorts non-ASCII initials (Ç, Ö, Ş, Ü) after Z; fine
    # for the seeded names, upgrade to locale-aware sorting when people can be added.
    return [_person(r) for r in db.fetch_all("SELECT * FROM people ORDER BY full_name")]


def get_person(db: Db, person_id: str) -> Result[Person]:
    row = db.fetch_one("SELECT * FROM people WHERE id = ?", (person_id,))
    return Ok(_person(row)) if row else Err(ErrorCode.NOT_FOUND)
