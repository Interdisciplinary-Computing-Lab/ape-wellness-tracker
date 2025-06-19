# Main app routes (e.g., homepage)

"""
Defines the main web routes for the Ape Wellness Tracker Flask application.

This module sets up the 'site' Blueprint and includes the root ('/') route,
which renders the homepage template.
"""

from flask import Blueprint, render_template

# Blueprint for site-wide routes
site = Blueprint('site', __name__)

@site.route('/')
def index():
    """
    Route for the homepage.

    Returns:
        Rendered HTML template for the index page.
    """
    return render_template('index.html')
