import sys
import os
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db


@pytest.fixture
def base_upload_dir():
    """Temporary upload directory for artifacts."""

    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def app_fixture(base_upload_dir):
    """Create and configure a new app instance for each test."""

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['BASE_UPLOAD_DIR'] = base_upload_dir

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_fixture):
    """A test client for the app."""

    return app_fixture.test_client()
