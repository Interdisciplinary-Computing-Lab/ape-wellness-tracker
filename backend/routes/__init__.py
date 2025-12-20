"""
Routes package for the Ape Wellness Tracker application.

This module consolidates all routes into a single 'site' blueprint
for backward compatibility with existing templates and URL references.
Routes are organized into separate modules but all register on the same blueprint.
"""

from flask import Blueprint

# Create the main site blueprint that all routes will register on
site = Blueprint('site', __name__)

# Import all route modules to register their routes on the site blueprint
# Each module imports 'site' from here and registers its routes
from backend.routes import dashboard
from backend.routes import apes
from backend.routes import recipes
from backend.routes import meals
from backend.routes import categories
from backend.routes import reports
from backend.routes import images
from backend.routes import users

# Export the site blueprint
__all__ = ['site']

