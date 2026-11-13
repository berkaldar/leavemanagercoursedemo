from datetime import date

from app.db import Db
from app.leave import plant_shutdowns, working_days

CHRISTMAS = (date(2026, 12, 24), date(2026, 12, 31))
SUMMER = (date(2027, 7, 26), date(2027, 8, 6))


def test_counts_weekdays_excluding_shutdowns() -> None:
    shutdowns = [CHRISTMAS, SUMMER]
    assert working_days(date(2026, 11, 16), date(2026, 11, 20), shutdowns) == 5
    assert working_days(date(2026, 11, 20), date(2026, 11, 23), shutdowns) == 2  # Fri … Mon
    assert working_days(date(2026, 12, 21), date(2026, 12, 31), shutdowns) == 3  # 21–23 Dec
    assert working_days(date(2026, 11, 18), date(2026, 11, 18), shutdowns) == 1


def test_no_working_days() -> None:
    shutdowns = [CHRISTMAS, SUMMER]
    assert working_days(date(2026, 11, 21), date(2026, 11, 22), shutdowns) == 0  # weekend
    assert working_days(*SUMMER, shutdowns) == 0
    assert working_days(date(2026, 11, 20), date(2026, 11, 19), shutdowns) == 0  # reversed


def test_seeded_shutdowns(db: Db) -> None:
    assert sorted(plant_shutdowns(db)) == [CHRISTMAS, SUMMER]
