"""The only package that imports sqlite3 (docs/architecture.md, rule 4)."""

import sqlite3
from pathlib import Path
from typing import Any

Row = dict[str, Any]

# Fixed ids so tests and demos can name the seeded people (spec 0001, R-1).
DENIZ_ID = "6f1c2b9e-4a7d-4e0a-9c3b-1d2e3f4a5b01"
ALI_ID = "6f1c2b9e-4a7d-4e0a-9c3b-1d2e3f4a5b02"
ELIF_ID = "6f1c2b9e-4a7d-4e0a-9c3b-1d2e3f4a5b03"
SEED_PEOPLE = [
    (DENIZ_ID, "Deniz Kaya", None),
    (ALI_ID, "Ali Demir", DENIZ_ID),
    (ELIF_ID, "Elif Şahin", DENIZ_ID),
]
# Invented plant reference data (docs/domain.md, BR-8; spec 0002, R-4).
SEED_SHUTDOWNS = [
    ("Christmas break", "2026-12-24", "2026-12-31"),
    ("Summer shutdown", "2027-07-26", "2027-08-06"),
]


class Db:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def fetch_all(self, sql: str, params: tuple[object, ...] = ()) -> list[Row]:
        return [dict(row) for row in self._connection.execute(sql, params)]

    def fetch_one(self, sql: str, params: tuple[object, ...] = ()) -> Row | None:
        row = self._connection.execute(sql, params).fetchone()
        return dict(row) if row else None

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> int:
        """Runs one statement in its own transaction; returns the number of rows it changed."""
        with self._connection:
            return self._connection.execute(sql, params).rowcount

    def close(self) -> None:
        self._connection.close()


def open_db(uri: str) -> Db:
    """`uri`: `file:leave.db`, or `file:<name>?mode=memory&cache=shared` in tests."""
    connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return Db(connection)


def migrate(db: Db) -> None:
    db._connection.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))


def seed(db: Db) -> None:
    for person in SEED_PEOPLE:
        db.execute(
            "INSERT OR IGNORE INTO people (id, full_name, manager_id) VALUES (?, ?, ?)", person
        )
    for shutdown in SEED_SHUTDOWNS:
        db.execute(
            "INSERT OR IGNORE INTO plant_shutdowns (name, start_date, end_date) VALUES (?, ?, ?)",
            shutdown,
        )
