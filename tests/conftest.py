"""Shared fixtures.

Each test gets its own SQLite file under a temporary folder. Nothing here
writes to data/farm_tracker.db.
"""

import pytest

from app import create_app
from app.db import connect, init_db


@pytest.fixture
def connection(tmp_path):
    """An empty database, already given its tables."""
    db = connect(tmp_path / "farm.db")
    init_db(db)
    yield db
    db.close()


@pytest.fixture
def app(tmp_path):
    application = create_app(db_path=tmp_path / "farm.db")
    application.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=True)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
