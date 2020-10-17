import os
import pytest

from flagging_site import create_app
from flagging_site import config as _config


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    if 'VAULT_PASSWORD' not in os.environ:
        os.environ['VAULT_PASSWORD'] = input('Enter vault password: ')
        import importlib
        importlib.reload(_config)

    app = create_app(config=_config.TestingConfig())
    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

