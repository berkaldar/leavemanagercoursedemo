import threading
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.db import ALI_ID, ELIF_ID, Db, migrate, open_db, seed
from app.leave import LeaveRequest, list_my_requests, submit_request
from app.people import Person
from app.result import Err, ErrorCode, Ok, Result

TODAY = date(2026, 11, 14)
NOW = datetime(2026, 11, 14, 7, 30, tzinfo=UTC)
ALI = Person(id=ALI_ID, full_name="Ali Demir", manager_id=None)
ELIF = Person(id=ELIF_ID, full_name="Elif Şahin", manager_id=None)


def submit(
    db: Db, start: date, end: date, *, actor: Person = ALI, leave_type: str = "Annual"
) -> Result[LeaveRequest]:
    return submit_request(db, actor, leave_type, start, end, TODAY, NOW)


def refused(db: Db, start: date, end: date) -> ErrorCode:
    result = submit(db, start, end)
    assert isinstance(result, Err)
    assert list_my_requests(db, ALI) == []  # nothing saved
    return result.code


def set_status(db: Db, status: str) -> None:
    db.execute("UPDATE leave_requests SET status = ?", (status,))


@pytest.mark.parametrize("leave_type", ["Annual", "Unpaid"])
def test_valid_request_is_pending(db: Db, leave_type: str) -> None:
    result = submit(db, date(2026, 11, 16), date(2026, 11, 20), leave_type=leave_type)
    assert isinstance(result, Ok)
    [stored] = list_my_requests(db, ALI)
    assert stored == result.value
    assert (stored.employee_id, stored.leave_type, stored.status, stored.working_days) == (
        ALI_ID,
        leave_type,
        "Pending",
        5,
    )


def test_created_at_is_the_injected_utc_instant(db: Db) -> None:
    assert isinstance(submit(db, date(2026, 11, 16), date(2026, 11, 20)), Ok)
    [row] = db.fetch_all("SELECT created_at FROM leave_requests")
    assert row["created_at"] == "2026-11-14T07:30:00+00:00"


def test_end_before_start_refused(db: Db) -> None:
    assert refused(db, date(2026, 11, 20), date(2026, 11, 19)) == ErrorCode.END_BEFORE_START
    assert isinstance(submit(db, date(2026, 11, 18), date(2026, 11, 18)), Ok)


def test_no_working_days_refused(db: Db) -> None:
    assert refused(db, date(2026, 11, 21), date(2026, 11, 22)) == ErrorCode.NO_WORKING_DAYS
    assert refused(db, date(2027, 7, 26), date(2027, 8, 6)) == ErrorCode.NO_WORKING_DAYS


def test_start_in_past_refused_today_allowed(db: Db) -> None:
    monday = date(2026, 11, 16)
    result = submit_request(db, ALI, "Annual", date(2026, 11, 13), monday, monday, NOW)
    assert isinstance(result, Err) and result.code == ErrorCode.START_IN_PAST
    assert isinstance(submit_request(db, ALI, "Annual", monday, monday, monday, NOW), Ok)


def test_spanning_two_years_refused(db: Db) -> None:
    assert refused(db, date(2026, 12, 21), date(2027, 1, 4)) == ErrorCode.SPANS_YEARS
    # The farthest date the boundary accepts: refused without walking ~8,000 years (F-3).
    assert refused(db, date(2026, 11, 16), date(9999, 12, 31)) == ErrorCode.SPANS_YEARS


def test_first_failing_reason_wins(db: Db) -> None:
    # End before start and in the past: R-5 order puts END_BEFORE_START first.
    assert refused(db, date(2026, 11, 10), date(2026, 11, 9)) == ErrorCode.END_BEFORE_START
    # A past weekend: no working days comes before the past start.
    assert refused(db, date(2026, 11, 7), date(2026, 11, 8)) == ErrorCode.NO_WORKING_DAYS


@pytest.mark.parametrize("status", ["Pending", "Approved"])
def test_overlap_rules(db: Db, status: str) -> None:
    assert isinstance(submit(db, date(2026, 11, 16), date(2026, 11, 20)), Ok)
    set_status(db, status)
    result = submit(db, date(2026, 11, 20), date(2026, 11, 24))
    assert isinstance(result, Err) and result.code == ErrorCode.OVERLAP
    assert len(list_my_requests(db, ALI)) == 1
    assert isinstance(submit(db, date(2026, 11, 23), date(2026, 11, 24)), Ok)


@pytest.mark.parametrize("status", ["Rejected", "Cancelled"])
def test_final_requests_do_not_block(db: Db, status: str) -> None:
    assert isinstance(submit(db, date(2026, 11, 16), date(2026, 11, 20)), Ok)
    set_status(db, status)
    assert isinstance(submit(db, date(2026, 11, 16), date(2026, 11, 20)), Ok)


def test_other_employees_requests_do_not_block(db: Db) -> None:
    assert isinstance(submit(db, date(2026, 11, 16), date(2026, 11, 20), actor=ELIF), Ok)
    result = submit(db, date(2026, 11, 16), date(2026, 11, 20))
    assert isinstance(result, Ok) and isinstance(result.value, LeaveRequest)


def test_concurrent_overlapping_submissions_store_one(tmp_path: Path) -> None:
    # A file DB as the app runs it (plan 0002, A-1): a shared-cache memory DB refuses a second
    # writer with "table is locked" instead of waiting, which the app never meets.
    uri = (tmp_path / "leave.db").as_uri()
    anchor = open_db(uri)
    migrate(anchor)
    seed(anchor)

    def submit_once(barrier: threading.Barrier, results: list[Result[LeaveRequest]]) -> None:
        db = open_db(uri)
        barrier.wait()
        results.append(submit(db, date(2026, 11, 16), date(2026, 11, 20)))
        db.close()

    for _ in range(10):
        anchor.execute("DELETE FROM leave_requests")
        barrier = threading.Barrier(2)
        results: list[Result[LeaveRequest]] = []
        threads = [threading.Thread(target=submit_once, args=(barrier, results)) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sorted(type(r).__name__ for r in results) == ["Err", "Ok"]
        assert [r.code for r in results if isinstance(r, Err)] == [ErrorCode.OVERLAP]
        assert len(list_my_requests(anchor, ALI)) == 1
    anchor.close()
