#!/usr/bin/env python3
"""
Role Management Script for Ape Wellness Tracker
Allows administrators to manage user roles and permissions.
"""

import sys
import uuid
from run import app
from backend.extensions import db
from backend.models.entry import User, Role
from flask_security.utils import hash_password

def list_users():
    """List all users and their roles"""
    with app.app_context():
        users = User.query.all()
        roles = Role.query.all()
        
        print("=== CURRENT ROLES ===")
        for role in roles:
            print(f"  - {role.name}: {role.description}")
        
        print(f"\n=== USERS ({len(users)} total) ===")
        for user in users:
            user_roles = [role.name for role in user.roles]
            status = "Active" if user.active else "Inactive"
            print(f"  - {user.email} ({status}) - Roles: {user_roles}")

def create_role(role_name, description=""):
    """Create a new role"""
    with app.app_context():
        existing_role = Role.query.filter_by(name=role_name).first()
        if existing_role:
            print(f"❌ Role '{role_name}' already exists")
            return False
        
        new_role = Role(name=role_name, description=description)
        db.session.add(new_role)
        db.session.commit()
        print(f"[SUCCESS] Role '{role_name}' created successfully")
        return True

def assign_role(user_email, role_name):
    """Assign a role to a user"""
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        role = Role.query.filter_by(name=role_name).first()
        
        if not user:
            print(f"[ERROR] User '{user_email}' not found")
            return False
        
        if not role:
            print(f"[ERROR] Role '{role_name}' not found")
            return False
        
        if role in user.roles:
            print(f"[WARNING] User '{user_email}' already has role '{role_name}'")
            return False
        
        user.roles.append(role)
        db.session.commit()
        print(f"[SUCCESS] Role '{role_name}' assigned to '{user_email}'")
        return True

def remove_role(user_email, role_name):
    """Remove a role from a user"""
    with app.app_context():
        user = User.query.filter_by(email=user_email).first()
        role = Role.query.filter_by(name=role_name).first()
        
        if not user:
            print(f"[ERROR] User '{user_email}' not found")
            return False
        
        if not role:
            print(f"[ERROR] Role '{role_name}' not found")
            return False
        
        if role not in user.roles:
            print(f"[WARNING] User '{user_email}' does not have role '{role_name}'")
            return False
        
        user.roles.remove(role)
        db.session.commit()
        print(f"[SUCCESS] Role '{role_name}' removed from '{user_email}'")
        return True

def create_user(email, password, make_admin=False):
    """Create a new user with optional admin role"""
    with app.app_context():
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"[ERROR] User '{email}' already exists")
            return False
        
        new_user = User(
            email=email,
            password=hash_password(password),
            active=True,
            fs_uniquifier=str(uuid.uuid4())
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        if make_admin:
            admin_role = Role.query.filter_by(name='Admin').first()
            if admin_role:
                new_user.roles.append(admin_role)
                db.session.commit()
                print(f"[SUCCESS] Admin user '{email}' created successfully")
            else:
                print(f"[SUCCESS] User '{email}' created successfully (Admin role not found)")
        else:
            print(f"[SUCCESS] User '{email}' created successfully")
        
        return True

def ensure_admin_role():
    """Ensure Admin role exists"""
    with app.app_context():
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator with full access')
            db.session.add(admin_role)
            db.session.commit()
            print("[SUCCESS] Admin role created")
        else:
            print("[SUCCESS] Admin role already exists")
        return admin_role

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("""
Ape Wellness Tracker - Role Management

Usage:
  python manage_roles.py list                           # List all users and roles
  python manage_roles.py create-role <name> [desc]      # Create a new role
  python manage_roles.py assign <email> <role>          # Assign role to user
  python manage_roles.py remove <email> <role>          # Remove role from user
  python manage_roles.py create-user <email> <password> [admin]  # Create user (optional admin)
  python manage_roles.py ensure-admin                   # Ensure Admin role exists

Examples:
  python manage_roles.py list
  python manage_roles.py create-role "Researcher" "Can view and log data"
  python manage_roles.py assign john@example.com Admin
  python manage_roles.py create-user researcher@ape.org password123 admin
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    
    elif command == "create-role":
        if len(sys.argv) < 3:
            print("[ERROR] Usage: python manage_roles.py create-role <name> [description]")
            return
        role_name = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        create_role(role_name, description)
    
    elif command == "assign":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python manage_roles.py assign <email> <role>")
            return
        user_email = sys.argv[2]
        role_name = sys.argv[3]
        assign_role(user_email, role_name)
    
    elif command == "remove":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python manage_roles.py remove <email> <role>")
            return
        user_email = sys.argv[2]
        role_name = sys.argv[3]
        remove_role(user_email, role_name)
    
    elif command == "create-user":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python manage_roles.py create-user <email> <password> [admin]")
            return
        email = sys.argv[2]
        password = sys.argv[3]
        make_admin = len(sys.argv) > 4 and sys.argv[4].lower() == "admin"
        create_user(email, password, make_admin)
    
    elif command == "ensure-admin":
        ensure_admin_role()
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Run 'python manage_roles.py' for usage information")

if __name__ == "__main__":
    main()
