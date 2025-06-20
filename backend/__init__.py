"""
Initializes the Flask app and registers blueprints for the Ape Initiative project.

This module sets up the core Flask application using the application factory pattern.
"""

from flask import Flask

def create_app():
    """
    Factory function to create and configure the Flask app.

    Returns:
        app (Flask): The configured Flask application instance.
    """
    app = Flask(__name__)

    from backend.routes.main import site
    app.register_blueprint(site)

    return app
