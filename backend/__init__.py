from flask import Flask
from backend.extensions import db
from backend.security import security, user_datastore
from backend.routes.main import site

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SECURITY_PASSWORD_SALT"] = "super-salty-salt"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False

    db.init_app(app)
    security.init_app(app, user_datastore)

    app.register_blueprint(site)

    with app.app_context():
        db.create_all()

    return app