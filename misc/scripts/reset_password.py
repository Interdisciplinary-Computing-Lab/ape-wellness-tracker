#!/usr/bin/env python3
"""
Reset a user's password (e.g. after SECRET_KEY / SECURITY_PASSWORD_SALT changed).

Usage (from project root):
  python misc/scripts/reset_password.py admin@apeinitiative.org newpassword
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend import create_app
from backend.extensions import db
from backend.models.entry import User
from flask_security.utils import hash_password


def main():
    if len(sys.argv) != 3:
        print("Usage: python misc/scripts/reset_password.py <email> <new-password>")
        return 1

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"No user found with email: {email}")
            print("Existing accounts:")
            for u in User.query.order_by(User.email).all():
                print(f"  - {u.email}")
            return 1

        user.password = hash_password(password)
        user.active = True
        if not user.fs_uniquifier:
            user.fs_uniquifier = str(uuid.uuid4())
        from datetime import datetime
        if not user.confirmed_at:
            user.confirmed_at = datetime.utcnow()
        db.session.commit()
        print(f"Password updated for {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
