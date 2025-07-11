"""
Initializes the Flask app and registers blueprints for the Ape Initiative project.

This module sets up the core Flask application using the application factory pattern.
"""

from flask import Flask
from backend.extensions import db

def create_app():
    """
    Factory function to create and configure the Flask app.

    Returns:
        app (Flask): The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


    db.init_app(app)

    from backend.routes.main import site
    app.register_blueprint(site)

    with app.app_context():
        db.create_all()

    return app
