"""Shared pytest fixtures."""

from datetime import datetime

import pytest
from flask_security.utils import hash_password

from backend import create_app
from backend.extensions import db
from backend.models.entry import Role, User


@pytest.fixture
def app(tmp_path):
    db_path = (tmp_path / "test.db").as_posix()
    application = create_app(
        testing=True,
        config_overrides={
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "WTF_CSRF_ENABLED": False,
            "SECURITY_REGISTERABLE": False,
        },
    )
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _add_user(email, password, role_name):
    role = Role.query.filter_by(name=role_name).first()
    user = User(
        email=email,
        password=hash_password(password),
        active=True,
        confirmed_at=datetime.utcnow(),
        fs_uniquifier=email,
    )
    if role:
        user.roles.append(role)
    db.session.add(user)
    db.session.commit()
    return {"email": email, "fs_uniquifier": user.fs_uniquifier}


@pytest.fixture
def admin_user(app):
    with app.app_context():
        return _add_user("admin@test.local", "AdminPass1!", "Admin")


@pytest.fixture
def researcher_user(app):
    with app.app_context():
        return _add_user("researcher@test.local", "Research1!", "Researcher")


@pytest.fixture
def viewer_user(app):
    with app.app_context():
        return _add_user("viewer@test.local", "ViewerPass1!", "Viewer")


def login(client, user_info):
    """Establish a Flask-Login session without posting the login form."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_info["fs_uniquifier"])
        sess["_fresh"] = True

