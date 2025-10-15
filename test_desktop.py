#!/usr/bin/env python3
"""
Test script to verify the desktop app components work without opening GUI
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from flaskwebgui import FlaskUI
        print("[OK] FlaskWebGUI imported successfully")
    except ImportError as e:
        print(f"[ERROR] FlaskWebGUI import failed: {e}")
        return False
    
    try:
        from backend import create_app
        print("[OK] Flask app imported successfully")
    except ImportError as e:
        print(f"[ERROR] Flask app import failed: {e}")
        return False
    
    return True

def test_flask_app():
    """Test that the Flask app can be created"""
    print("\nTesting Flask app creation...")
    
    try:
        from backend import create_app
        app = create_app()
        print("[OK] Flask app created successfully")
        
        # Test that we can get the app config
        print(f"[OK] Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
        print(f"[OK] Secret Key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Flask app creation failed: {e}")
        return False

def test_flaskwebgui():
    """Test FlaskWebGUI initialization"""
    print("\nTesting FlaskWebGUI initialization...")
    
    try:
        from flaskwebgui import FlaskUI
        from backend import create_app
        
        app = create_app()
        ui = FlaskUI(
            app=app,
            server="flask",
            width=1200,
            height=800,
            fullscreen=False
        )
        print("[OK] FlaskWebGUI initialized successfully")
        print("[OK] Desktop app is ready to run")
        
        return True
    except Exception as e:
        print(f"[ERROR] FlaskWebGUI initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("APE WELLNESS TRACKER - DESKTOP APP TEST")
    print("=" * 45)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test Flask app
    if not test_flask_app():
        all_tests_passed = False
    
    # Test FlaskWebGUI
    if not test_flaskwebgui():
        all_tests_passed = False
    
    print("\n" + "=" * 45)
    if all_tests_passed:
        print("[SUCCESS] ALL TESTS PASSED!")
        print("The desktop app is ready to run.")
        print("\nTo start the app, run:")
        print("  python desktop_app.py")
    else:
        print("[FAILED] SOME TESTS FAILED!")
        print("Please fix the issues above before distributing.")
    
    return all_tests_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
