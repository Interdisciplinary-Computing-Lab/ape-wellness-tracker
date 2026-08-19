#!/usr/bin/env python3
"""Create an admin user. Never uses a default password."""

import argparse
import os
import sys
import uuid

from flask_security.utils import hash_password

from run import app
from backend.extensions import db
from backend.models.entry import Role, User
from backend.utils.password_policy import validate_password


def _ensure_admin_role():
    admin_role = Role.query.filter_by(name="Admin").first()
    if admin_role:
        return admin_role
    admin_role = Role(name="Admin", description="Administrator with full access")
    db.session.add(admin_role)
    db.session.commit()
    return admin_role


def create_admin_user(email, password):
    policy_errors = validate_password(password)
    if policy_errors:
        print("Password does not meet the policy:")
        for error in policy_errors:
            print(f"  - {error}")
        return 1

    with app.app_context():
        admin_role = _ensure_admin_role()
        existing = User.query.filter_by(email=email).first()
        if existing:
            if admin_role not in existing.roles:
                existing.roles.append(admin_role)
                db.session.commit()
                print(f"Granted Admin to existing user {email}")
            else:
                print(f"{email} already has the Admin role")
            return 0

        admin_user = User(
            email=email,
            password=hash_password(password),
            active=True,
            fs_uniquifier=str(uuid.uuid4()),
        )
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Created admin user {email}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Create or promote an Admin user")
    parser.add_argument(
        "--email",
        default=os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@apeinitiative.org"),
        help="Admin email (or BOOTSTRAP_ADMIN_EMAIL)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
        help="Admin password (or BOOTSTRAP_ADMIN_PASSWORD)",
    )
    args = parser.parse_args()
    if not args.password:
        print(
            "Provide --password or set BOOTSTRAP_ADMIN_PASSWORD. "
            "A default password is not allowed."
        )
        return 1
    return create_admin_user(args.email.strip(), args.password)


if __name__ == "__main__":
    sys.exit(main())
