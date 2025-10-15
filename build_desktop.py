#!/usr/bin/env python3
"""
Build script for creating a standalone desktop executable

This script uses PyInstaller to create a standalone executable
of the Ape Wellness Tracker desktop application.

Usage:
    python build_desktop.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building desktop executable...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window on Windows
        "--name", "ApeWellnessTracker",
        # "--icon", "backend/static/images/bonobo-placeholder.jpg",  # App icon (commented out due to format issue)
        "--add-data", "backend;backend",  # Include backend directory
        "--add-data", "instance;instance",  # Include instance directory
        "--add-data", "backend/templates;backend/templates",  # Include templates
        "--add-data", "backend/static;backend/static",  # Include static files
        "--hidden-import", "flaskwebgui",
        "--hidden-import", "flask",
        "--hidden-import", "flask_security",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "bcrypt",
        "desktop_app.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def create_installer_script():
    """Create a simple installer script"""
    installer_content = '''@echo off
echo Installing Ape Wellness Tracker Desktop App...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create desktop shortcut (Windows)
if exist "%USERPROFILE%\\Desktop" (
    echo Creating desktop shortcut...
    echo [InternetShortcut] > "%USERPROFILE%\\Desktop\\Ape Wellness Tracker.url"
    echo URL=file:///%CD%\\launch_desktop.py >> "%USERPROFILE%\\Desktop\\Ape Wellness Tracker.url"
    echo IconFile=%CD%\\backend\\static\\images\\bonobo-placeholder.jpg >> "%USERPROFILE%\\Desktop\\Ape Wellness Tracker.url"
)

echo.
echo Installation complete!
echo You can now run the application using launch_desktop.py
pause
'''
    
    with open('install_desktop.bat', 'w') as f:
        f.write(installer_content)
    
    print("Created install_desktop.bat")

def main():
    """Main build function"""
    print("Ape Wellness Tracker - Desktop Build Script")
    print("=" * 45)
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build executable
    if build_executable():
        print("\nBuild successful!")
        print("Executable created in: dist/ApeWellnessTracker.exe")
        
        # Create installer script
        create_installer_script()
        
        print("\nNext steps:")
        print("1. Test the executable: dist/ApeWellnessTracker.exe")
        print("2. Distribute the entire 'dist' folder")
        print("3. Or use install_desktop.bat for easy installation")
    else:
        print("Build failed. Please check the error messages above.")

if __name__ == '__main__':
    main()
