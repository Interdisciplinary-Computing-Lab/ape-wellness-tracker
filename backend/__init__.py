from flask import Flask
import os
from backend.extensions import db
from backend.security import init_security
from backend.routes.main import site

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='static', static_url_path='/static')

    # Ensure SQLite DB path resolves to the instance directory for cross-OS consistency
    db_path = os.path.join(app.instance_path, 'database.db').replace('\\', '/')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SECURITY_PASSWORD_SALT"] = "super-salty-salt"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False


    db.init_app(app)
    init_security(app)

    app.register_blueprint(site)

    with app.app_context():
        db.create_all()

    return app