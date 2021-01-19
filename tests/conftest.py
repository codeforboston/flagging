import os
import pytest

from flagging_site import create_app


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(config='testing')
    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
