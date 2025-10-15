#!/usr/bin/env python3
"""
Ape Synchronization Script for New Users
Ensures new users have access to the standard ape population.
"""

from run import app
from backend.extensions import db
from backend.models.entry import Apes, User
from datetime import date

def get_standard_apes():
    """Get the list of standard apes that should be available to all users"""
    return [
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

def ensure_standard_apes():
    """Ensure all standard apes exist in the database"""
    with app.app_context():
        standard_apes = get_standard_apes()
        created_count = 0
        existing_count = 0
        
        for ape_data in standard_apes:
            existing_ape = Apes.query.filter_by(ape_name=ape_data['ape_name']).first()
            
            if not existing_ape:
                new_ape = Apes(**ape_data)
                db.session.add(new_ape)
                created_count += 1
                print(f"✅ Created ape: {ape_data['ape_name']}")
            else:
                existing_count += 1
                print(f"ℹ️  Ape already exists: {ape_data['ape_name']}")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n✅ Created {created_count} new apes")
        
        print(f"ℹ️  {existing_count} apes already existed")
        return created_count + existing_count

def sync_apes_for_user(user_email=None):
    """Sync apes for a specific user (or all users if no email provided)"""
    with app.app_context():
        # First ensure all standard apes exist
        total_apes = ensure_standard_apes()
        
        if user_email:
            user = User.query.filter_by(email=user_email).first()
            if not user:
                print(f"❌ User '{user_email}' not found")
                return False
            users = [user]
        else:
            users = User.query.all()
        
        print(f"\n=== APE ACCESS FOR USERS ===")
        for user in users:
            # Since apes are global, all users automatically have access to all apes
            active_apes = Apes.query.filter_by(is_archived=False).count()
            archived_apes = Apes.query.filter_by(is_archived=True).count()
            
            print(f"User: {user.email}")
            print(f"  - Active apes: {active_apes}")
            print(f"  - Archived apes: {archived_apes}")
            print(f"  - Total apes: {active_apes + archived_apes}")
        
        return True

def list_ape_access():
    """List ape access for all users"""
    with app.app_context():
        users = User.query.all()
        apes = Apes.query.all()
        
        print("=== APE POPULATION ===")
        for ape in apes:
            status = "Archived" if ape.is_archived else "Active"
            print(f"  - {ape.ape_name} ({status}) - Age: {ape.age}, Weight: {ape.weight}kg")
        
        print(f"\n=== USER ACCESS ===")
        print(f"Total users: {len(users)}")
        print(f"Total apes: {len(apes)}")
        print(f"Active apes: {len([a for a in apes if not a.is_archived])}")
        print(f"Archived apes: {len([a for a in apes if a.is_archived])}")
        
        print("\nNote: All users have access to all apes (global ape population)")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("""
Ape Synchronization Script

Usage:
  python sync_apes_for_user.py ensure                    # Ensure all standard apes exist
  python sync_apes_for_user.py sync [email]              # Sync apes for user (or all users)
  python sync_apes_for_user.py list                      # List ape access for all users

Examples:
  python sync_apes_for_user.py ensure
  python sync_apes_for_user.py sync
  python sync_apes_for_user.py sync researcher@ape.org
  python sync_apes_for_user.py list
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "ensure":
        ensure_standard_apes()
    
    elif command == "sync":
        user_email = sys.argv[2] if len(sys.argv) > 2 else None
        sync_apes_for_user(user_email)
    
    elif command == "list":
        list_ape_access()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python sync_apes_for_user.py' for usage information")

if __name__ == "__main__":
    main()
