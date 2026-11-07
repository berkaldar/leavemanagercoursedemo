from app.db import ALI_ID, DENIZ_ID, ELIF_ID, Db
from app.people import get_person, list_people
from app.result import Err, ErrorCode, Ok


def test_list_people_sorted_by_full_name(db: Db) -> None:
    assert [p.full_name for p in list_people(db)] == ["Ali Demir", "Deniz Kaya", "Elif Şahin"]


def test_seeded_reports_have_deniz_as_manager(db: Db) -> None:
    managers = {p.id: p.manager_id for p in list_people(db)}
    assert managers == {DENIZ_ID: None, ALI_ID: DENIZ_ID, ELIF_ID: DENIZ_ID}


def test_get_person_returns_seeded_person(db: Db) -> None:
    result = get_person(db, ELIF_ID)
    assert isinstance(result, Ok)
    assert result.value.full_name == "Elif Şahin"


def test_get_person_unknown_is_not_found(db: Db) -> None:
    assert get_person(db, "not-a-person") == Err(ErrorCode.NOT_FOUND)
