import os
import pytest

from flagging_site import create_app
from flagging_site.data.database import cache as _cache

from flagging_site.data.database import create_db
from flagging_site.data.database import delete_db
from flagging_site.data.database import init_db
from flagging_site.data.database import update_db


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(config='testing')
    with app.app_context():
        create_db(overwrite=True)
        init_db()
        update_db()
        yield app


@pytest.fixture
def live_app(app):
    app.config['USE_MOCK_DATA'], old = False, app.config['USE_MOCK_DATA']
    yield app
    app.config['USE_MOCK_DATA'] = old


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function', autouse=True)
def cache():
    yield _cache
    _cache.clear()


@pytest.fixture(scope='session')
def _db(app):
    from flagging_site.data.database import db
    yield db



