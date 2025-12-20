#!/usr/bin/env python3
"""
Database initialization script for Ape Wellness Tracker
Creates all tables with the correct schema.
"""

from run import app
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals, User, Role

def init_db():
    """Initialize the database with all tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 