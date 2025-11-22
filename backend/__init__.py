import os
from flask import Flask
from backend.extensions import db
from backend.security import init_security
from backend.routes.main import site

def create_app():
    # Ensure instance folder exists
    backend_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(backend_dir)
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Use absolute path for static folder
    static_folder = os.path.join(backend_dir, 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static', instance_path=instance_path)
    
    # Use instance folder for database
    database_path = os.path.join(instance_path, 'database.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
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