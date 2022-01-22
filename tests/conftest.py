import pytest

from unittest.mock import patch
from app.main import create_app
from app.twitter import tweepy_api
from app.data.database import init_db
from app.data.processing.core import update_db
from app.data.globals import cache as _cache
from flask import g
from pytest_postgresql.janitor import DatabaseJanitor


@pytest.fixture(scope='session')
def app():
    app = create_app(config='testing')

    janitor = DatabaseJanitor(
        user=app.config['POSTGRES_USER'],
        password=app.config['POSTGRES_PASSWORD'],
        host=app.config['POSTGRES_HOST'],
        port=app.config['POSTGRES_PORT'],
        dbname=app.config['POSTGRES_DB'],
        version=12
    )

    try:
        janitor.drop()
    except Exception:
        pass

    janitor.init()
    with app.app_context():
        yield app
    janitor.drop()


@pytest.fixture
def live_app(app):
    """This takes the app instance, and temporarily sets `USE_MOCK_DATA` to
    False. We can use this for tests where `USE_MOCK_DATA` needs to be False.
    """
    app.config['USE_MOCK_DATA'], old = False, app.config['USE_MOCK_DATA']
    yield app
    app.config['USE_MOCK_DATA'] = old


@pytest.fixture(scope='function')
def client(app):
    """A test client for the app. You can think of the test like a web browser;
    it retrieves data from the website in a similar way that a browser would.
    """
    return app.test_client()


@pytest.fixture(scope='function', autouse=True)
def cache():
    """After every test, we want to clear the cache."""
    yield _cache
    _cache.clear()


@pytest.fixture(scope='session')
def _db(app):
    """See this:

    https://github.com/jeancochrane/pytest-flask-sqlalchemy

    Basically, this '_db' fixture is required for the above extension to work.
    We use that extension to allow for easy testing of the database.
    """
    from app.data.database import db
    with app.app_context():
        init_db()
        update_db()
    yield db


@pytest.fixture
def cli_runner(app):
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def mock_send_tweet():
    with patch.object(tweepy_api, 'update_status') as mocked_func:
        yield mocked_func


@pytest.fixture(scope='function', autouse=True)
def monkeypatch_globals(db_session):
    yield
    for o in ['website_options', 'boathouse_list', 'reach_list']:
        if o in g:
            g.pop(o)
