from flask import Flask
from backend.extensions import db
from backend.security import init_security
from backend.routes.main import site

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SECURITY_PASSWORD_SALT"] = "super-salty-salt"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
    
    # Configure post-login redirect
    app.config["SECURITY_POST_LOGIN_REDIRECT_ENDPOINT"] = "site.dashboard"
    app.config["SECURITY_POST_LOGOUT_REDIRECT_ENDPOINT"] = "security.login"

    db.init_app(app)
    init_security(app)

    app.register_blueprint(site)

    with app.app_context():
        db.create_all()

    return app