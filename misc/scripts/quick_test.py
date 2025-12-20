#!/usr/bin/env python3
"""
Quick test script to verify the system is working correctly
"""

from run import app
from backend.extensions import db
from backend.models.entry import User, Apes, Role

def quick_test():
    """Run a quick test of the system"""
    with app.app_context():
        print("=== QUICK SYSTEM TEST ===")
        
        # Test 1: Check if apes exist
        apes = Apes.query.filter_by(is_archived=False).all()
        print(f"1. Active Apes: {len(apes)}")
        if len(apes) == 0:
            print("   [PROBLEM] No active apes found!")
            print("   Solution: Run 'python sync_apes_for_user.py ensure'")
        else:
            print("   [OK] Apes are available")
            for ape in apes:
                print(f"      - {ape.ape_name}")
        
        # Test 2: Check if users exist
        users = User.query.all()
        print(f"\n2. Users: {len(users)}")
        if len(users) == 0:
            print("   [PROBLEM] No users found!")
            print("   Solution: Run 'python create_admin.py'")
        else:
            print("   [OK] Users exist")
            for user in users:
                roles = [role.name for role in user.roles]
                print(f"      - {user.email} (Roles: {roles})")
        
        # Test 3: Check if admin role exists
        admin_role = Role.query.filter_by(name='Admin').first()
        print(f"\n3. Admin Role: {'EXISTS' if admin_role else 'MISSING'}")
        if not admin_role:
            print("   [PROBLEM] Admin role not found!")
            print("   Solution: Run 'python setup_system.py'")
        else:
            print("   [OK] Admin role exists")
        
        # Test 4: Check if any user has admin role
        admin_users = [user for user in users if admin_role and admin_role in user.roles]
        print(f"\n4. Admin Users: {len(admin_users)}")
        if len(admin_users) == 0:
            print("   [PROBLEM] No users have admin role!")
            print("   Solution: Run 'python manage_roles.py assign <email> Admin'")
        else:
            print("   [OK] Admin users exist")
            for user in admin_users:
                print(f"      - {user.email}")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        if len(apes) > 0 and len(users) > 0 and admin_role and len(admin_users) > 0:
            print("[SUCCESS] System is properly configured!")
            print("New users should be able to see apes and log feeding sessions.")
            print("Only admin users can delete apes.")
        else:
            print("[ISSUES FOUND] System needs configuration.")
            print("Run 'python setup_system.py' to fix all issues.")

if __name__ == "__main__":
    quick_test()
