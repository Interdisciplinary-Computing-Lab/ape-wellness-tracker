#!/usr/bin/env python3
"""
Complete System Setup Script for Ape Wellness Tracker
Sets up roles, users, and ensures ape population is ready.
"""

import sys
import uuid
from run import app
from backend.extensions import db
from backend.models.entry import User, Role, Apes
from flask_security.utils import hash_password
from datetime import date

def setup_roles():
    """Set up standard roles for the system"""
    with app.app_context():
        roles_to_create = [
            ('Admin', 'Administrator with full access to all features'),
            ('Researcher', 'Can view and log feeding data for all apes'),
            ('Viewer', 'Can view data but cannot log feeding sessions')
        ]
        
        created_roles = []
        for role_name, description in roles_to_create:
            existing_role = Role.query.filter_by(name=role_name).first()
            if not existing_role:
                new_role = Role(name=role_name, description=description)
                db.session.add(new_role)
                created_roles.append(role_name)
                print(f"✅ Created role: {role_name}")
            else:
                print(f"ℹ️  Role already exists: {role_name}")
        
        if created_roles:
            db.session.commit()
            print(f"\n✅ Created {len(created_roles)} new roles")
        
        return len(created_roles)

def setup_apes():
    """Set up standard ape population"""
    with app.app_context():
        standard_apes = [
            {
                'ape_name': 'MAISHA',
                'birthday': date(2000, 5, 28),
                'weight': 42.5,
                'mother': 'Matata',
                'image_filename': 'maisha.jpg'
            },
            {
                'ape_name': 'TECO',
                'birthday': date(2010, 6, 1),
                'weight': 38.2,
                'mother': None,
                'image_filename': 'teco.jpg'
            },
            {
                'ape_name': 'NYOTA',
                'birthday': date(1998, 4, 4),
                'weight': 45.8,
                'mother': None,
                'image_filename': 'nyota.jpg'
            },
            {
                'ape_name': 'CLARA',
                'birthday': date(2010, 5, 27),
                'weight': 39.1,
                'mother': None,
                'image_filename': 'clara.jpg'
            },
            {
                'ape_name': 'MALI',
                'birthday': date(2007, 9, 4),
                'weight': 41.3,
                'mother': None,
                'image_filename': 'mali.jpg'
            },
            {
                'ape_name': 'ELIKYA',
                'birthday': date(1997, 6, 28),
                'weight': 44.7,
                'mother': 'Matata',
                'image_filename': 'elikya.jpg'
            }
        ]
        
        created_apes = []
        for ape_data in standard_apes:
            existing_ape = Apes.query.filter_by(ape_name=ape_data['ape_name']).first()
            if not existing_ape:
                new_ape = Apes(**ape_data)
                db.session.add(new_ape)
                created_apes.append(ape_data['ape_name'])
                print(f"✅ Created ape: {ape_data['ape_name']}")
            else:
                print(f"ℹ️  Ape already exists: {ape_data['ape_name']}")
        
        if created_apes:
            db.session.commit()
            print(f"\n✅ Created {len(created_apes)} new apes")
        
        return len(created_apes)

def setup_admin_user():
    """Set up admin user if none exists"""
    with app.app_context():
        existing_users = User.query.all()
        
        if not existing_users:
            print("No users found. Creating admin user...")
            
            admin_user = User(
                email='admin@apeinitiative.org',
                password=hash_password('admin123'),
                active=True,
                fs_uniquifier=str(uuid.uuid4())
            )
            
            # Assign admin role
            admin_role = Role.query.filter_by(name='Admin').first()
            if admin_role:
                admin_user.roles.append(admin_role)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("Email: admin@apeinitiative.org")
            print("Password: admin123")
            print("Role: Admin")
            return True
        else:
            print(f"ℹ️  {len(existing_users)} users already exist")
            
            # Check if any user has admin role
            admin_role = Role.query.filter_by(name='Admin').first()
            if admin_role:
                admin_users = [user for user in existing_users if admin_role in user.roles]
                if not admin_users:
                    print("⚠️  No users have admin role. Making first user admin...")
                    first_user = existing_users[0]
                    first_user.roles.append(admin_role)
                    db.session.commit()
                    print(f"✅ {first_user.email} is now an admin!")
                else:
                    print(f"✅ {len(admin_users)} admin user(s) found")
            return False

def system_status():
    """Display current system status"""
    with app.app_context():
        users = User.query.all()
        roles = Role.query.all()
        apes = Apes.query.all()
        
        print("\n" + "="*50)
        print("SYSTEM STATUS")
        print("="*50)
        
        print(f"Users: {len(users)}")
        for user in users:
            user_roles = [role.name for role in user.roles]
            status = "Active" if user.active else "Inactive"
            print(f"  - {user.email} ({status}) - Roles: {user_roles}")
        
        print(f"\nRoles: {len(roles)}")
        for role in roles:
            print(f"  - {role.name}: {role.description}")
        
        print(f"\nApes: {len(apes)}")
        active_apes = [ape for ape in apes if not ape.is_archived]
        archived_apes = [ape for ape in apes if ape.is_archived]
        print(f"  - Active: {len(active_apes)}")
        print(f"  - Archived: {len(archived_apes)}")
        
        for ape in active_apes:
            print(f"    * {ape.ape_name} (Age: {ape.age}, Weight: {ape.weight}kg)")

def main():
    """Main setup function"""
    print("🐒 Ape Wellness Tracker - System Setup")
    print("="*50)
    
    with app.app_context():
        # Set up roles
        print("\n1. Setting up roles...")
        setup_roles()
        
        # Set up apes
        print("\n2. Setting up ape population...")
        setup_apes()
        
        # Set up admin user
        print("\n3. Setting up admin user...")
        setup_admin_user()
        
        # Display status
        system_status()
        
        print("\n" + "="*50)
        print("✅ SYSTEM SETUP COMPLETE!")
        print("="*50)
        print("\nNext steps:")
        print("1. Run the application: python run.py")
        print("2. Login with admin credentials")
        print("3. Create additional users as needed")
        print("4. Use 'python manage_roles.py' to manage user roles")
        print("5. Use 'python sync_apes_for_user.py' to manage ape population")

if __name__ == "__main__":
    main()
