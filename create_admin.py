#!/usr/bin/env python3
"""
Script to create an admin user or assign admin role to existing users
"""

import uuid
from run import app
from backend.extensions import db
from backend.models.entry import User, Role
from flask_security.utils import hash_password

def create_admin_user():
    """Create an admin user or assign admin role to existing users"""
    with app.app_context():
        # Check if Admin role exists, create if not
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Creating Admin role...")
            admin_role = Role(name='Admin', description='Administrator with full access')
            db.session.add(admin_role)
            db.session.commit()
            print("✅ Admin role created successfully!")
        else:
            print("✅ Admin role already exists")
        
        # Check existing users
        existing_users = User.query.all()
        print(f"\nFound {len(existing_users)} existing users:")
        
        for user in existing_users:
            roles = [role.name for role in user.roles]
            print(f"  - {user.email} (Active: {user.active}, Roles: {roles})")
            
            # Check if user already has admin role
            if admin_role in user.roles:
                print(f"    ✅ {user.email} already has Admin role")
            else:
                # Ask if user should be made admin
                print(f"    ❌ {user.email} does not have Admin role")
        
        # Create new admin user if no users exist
        if not existing_users:
            print("\nNo users found. Creating admin user...")
            
            admin_user = User(
                email='admin@apeinitiative.org',
                password=hash_password('admin123'),
                active=True,
                fs_uniquifier=str(uuid.uuid4())
            )
            
            # Assign admin role
            admin_user.roles.append(admin_role)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("Email: admin@apeinitiative.org")
            print("Password: admin123")
            print("Role: Admin")
        
        # If users exist, offer to make them admin
        elif existing_users:
            print("\nTo give admin access to an existing user, run:")
            print("python3 make_user_admin.py <email>")
            
            # Automatically make the first user admin if they don't have the role
            first_user = existing_users[0]
            if admin_role not in first_user.roles:
                print(f"\nMaking {first_user.email} an admin...")
                first_user.roles.append(admin_role)
                db.session.commit()
                print(f"✅ {first_user.email} is now an admin!")

if __name__ == "__main__":
    create_admin_user() 