from collections.abc import Iterator
from uuid import uuid4

import pytest

from app.db import Db, migrate, open_db, seed


def memory_db_uri() -> str:
    return f"file:test-{uuid4()}?mode=memory&cache=shared"


@pytest.fixture
def db() -> Iterator[Db]:
    database = open_db(memory_db_uri())
    migrate(database)
    seed(database)
    yield database
    database.close()
