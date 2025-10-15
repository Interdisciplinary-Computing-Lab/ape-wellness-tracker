#!/usr/bin/env python3
"""
Simple launcher script for the Ape Wellness Tracker Desktop App

This script provides a simple way to launch the desktop application
with proper error handling and dependency checking.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flaskwebgui
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install missing dependencies"""
    print("Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main launcher function"""
    print("Ape Wellness Tracker - Desktop Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("desktop_app.py").exists():
        print("Error: desktop_app.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("Failed to install dependencies. Please run: pip install -r requirements.txt")
            sys.exit(1)
    
    # Launch the desktop app
    print("Launching desktop application...")
    try:
        import desktop_app
        desktop_app.main()
    except Exception as e:
        print(f"Error launching desktop app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
