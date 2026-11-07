from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import ALI_ID, ELIF_ID
from app.main import create_app
from tests.conftest import memory_db_uri


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(memory_db_uri(), session_secret="test-secret")
    yield TestClient(app)
    app.state.anchor.close()


def login(client: TestClient, person_id: str) -> None:
    assert client.post("/api/session", json={"person_id": person_id}).status_code == 204


def assert_not_logged_in(client: TestClient) -> None:
    for path in ("/api/me", "/api/my/requests"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["error"] == "NOT_LOGGED_IN"
        assert "Elif" not in response.text and "Ali" not in response.text


def test_people_list_is_open_and_sorted(client: TestClient) -> None:
    names = [p["full_name"] for p in client.get("/api/people").json()]
    assert names == ["Ali Demir", "Deniz Kaya", "Elif Şahin"]


def test_login_then_me_returns_person(client: TestClient) -> None:
    login(client, ELIF_ID)
    assert client.get("/api/me").json() == {"id": ELIF_ID, "full_name": "Elif Şahin"}
    assert client.get("/api/my/requests").json() == {"requests": []}


def test_no_session_is_refused(client: TestClient) -> None:
    assert_not_logged_in(client)


def test_forged_session_cookie_is_refused(client: TestClient) -> None:
    client.cookies.set("session", "forged")
    assert_not_logged_in(client)


def test_login_unknown_person_refused(client: TestClient) -> None:
    response = client.post("/api/session", json={"person_id": "not-a-person"})
    assert (response.status_code, response.json()["error"]) == (404, "NOT_FOUND")
    assert_not_logged_in(client)


def test_login_with_unexpected_fields_refused(client: TestClient) -> None:
    response = client.post("/api/session", json={"person_id": ALI_ID, "role": "Manager"})
    assert (response.status_code, response.json()["error"]) == (422, "INVALID_INPUT")
    assert_not_logged_in(client)


def test_logout_ends_session(client: TestClient) -> None:
    login(client, ALI_ID)
    old_cookie = client.cookies["session"]
    assert client.delete("/api/session").status_code == 204
    assert_not_logged_in(client)
    client.cookies.set("session", old_cookie)  # a copied cookie must not outlive the logout
    assert_not_logged_in(client)


def test_new_login_retires_the_previous_session(client: TestClient) -> None:
    login(client, ALI_ID)
    old_cookie = client.cookies["session"]
    login(client, ELIF_ID)
    client.cookies.set("session", old_cookie)
    assert_not_logged_in(client)


def test_refused_login_retires_the_previous_session(client: TestClient) -> None:
    login(client, ALI_ID)
    old_cookie = client.cookies["session"]
    assert client.post("/api/session", json={"person_id": "not-a-person"}).status_code == 404
    client.cookies.set("session", old_cookie)
    assert_not_logged_in(client)


def test_responses_carry_content_security_policy(client: TestClient) -> None:
    assert client.get("/api/people").headers["content-security-policy"] == "default-src 'self'"


def test_unexpected_error_is_generic_and_carries_csp() -> None:
    app = create_app(memory_db_uri(), session_secret="test-secret")

    def boom() -> None:
        raise RuntimeError("SELECT secret FROM people")

    app.add_api_route("/api/boom", boom)
    app.router.routes.insert(0, app.router.routes.pop())  # ahead of the static mount at "/"
    response = TestClient(app, raise_server_exceptions=False).get("/api/boom")
    app.state.anchor.close()
    assert response.status_code == 500
    assert response.json() == {"error": "INTERNAL", "message": "Something went wrong."}
    assert response.headers["content-security-policy"] == "default-src 'self'"
