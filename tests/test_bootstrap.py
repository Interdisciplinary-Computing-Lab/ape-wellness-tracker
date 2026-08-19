from backend import create_app
from backend.models.entry import User


def test_bootstrap_admin_requires_env_password(tmp_path, monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    db_path = (tmp_path / "boot.db").as_posix()
    app = create_app(
        testing=True,
        config_overrides={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"},
    )
    with app.app_context():
        assert User.query.count() == 0


def test_bootstrap_admin_created_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "Bootstrap1!")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "ops@apeinitiative.org")
    db_path = (tmp_path / "boot2.db").as_posix()
    app = create_app(
        testing=True,
        config_overrides={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"},
    )
    with app.app_context():
        user = User.query.filter_by(email="ops@apeinitiative.org").first()
        assert user is not None
        assert user.has_role("Admin")
