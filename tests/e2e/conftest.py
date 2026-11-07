"""Browser journeys against a live app (docs/testing.md, e2e).

uvicorn runs in a thread inside the pytest process — no child process, so a crash cannot orphan
the server. Every test gets a fresh seeded memory database and no live sessions.
"""

import socket
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI

from app.db import migrate, open_db, seed
from app.main import create_app
from tests.conftest import memory_db_uri

E2E_DIR = "tests/e2e/"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # The fast/full selector (docs/testing.md, Two speeds rule 4): everything here is `e2e`.
    for item in items:
        if E2E_DIR in item.path.as_posix():
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def live_app() -> Iterator[tuple[FastAPI, str]]:
    app = create_app(memory_db_uri(), session_secret="e2e-secret")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]})
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        assert thread.is_alive() and time.monotonic() < deadline, "app under test did not start"
        time.sleep(0.01)
    try:
        yield app, f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        app.state.anchor.close()


@pytest.fixture(scope="session")
def base_url(live_app: tuple[FastAPI, str]) -> str:
    return live_app[1]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    # Determinism (docs/testing.md): fixed zone and locale, motion off.
    return {
        **browser_context_args,
        "timezone_id": "UTC",
        "locale": "en-US",
        "reduced_motion": "reduce",
    }


@pytest.fixture(autouse=True)
def fresh_data(live_app: tuple[FastAPI, str]) -> None:
    app = live_app[0]
    old_anchor = app.state.anchor
    app.state.db_uri = memory_db_uri()
    app.state.anchor = open_db(app.state.db_uri)
    migrate(app.state.anchor)
    seed(app.state.anchor)
    app.state.sessions.clear()
    old_anchor.close()
