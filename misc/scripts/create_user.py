#!/usr/bin/env python3
"""
Script to create a test user for the Ape Wellness Tracker
"""

import os
import sys
import uuid
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend import create_app
from backend.extensions import db
from backend.models.entry import User, Role
from flask_security.utils import hash_password

def create_test_user():
    """Create a test user if none exists"""
    app = create_app()
    with app.app_context():
        # Check if any users exist
        existing_users = User.query.all()
        print(f"Found {len(existing_users)} existing users:")
        
        for user in existing_users:
            print(f"  - {user.email} (Active: {user.active})")
        
        if not existing_users:
            print("\nNo users found. Creating test user...")
            
            # Create a test user
            test_user = User(
                email='admin@apeinitiative.org',
                password=hash_password('password123'),
                active=True,
                fs_uniquifier=str(uuid.uuid4())
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            print(" Test user created successfully!")
            print("Email: admin@apeinitiative.org")
            print("Password: password123")
        else:
            print("\nUsers already exist. You can use any of the above emails to log in.")

if __name__ == "__main__":
    create_test_user() 