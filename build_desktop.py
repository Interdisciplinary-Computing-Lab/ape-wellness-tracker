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
    
    # Determine the separator for add-data based on OS
    if sys.platform == 'win32':
        sep = ';'
    else:
        sep = ':'
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window on Windows
        "--name", "ApeWellnessTracker",
        # "--icon", "backend/static/images/bonobo-placeholder.jpg",  # App icon (commented out due to format issue)
        "--add-data", f"backend{sep}backend",  # Include backend directory
        "--add-data", f"backend/templates{sep}backend/templates",  # Include templates
        "--add-data", f"backend/static{sep}backend/static",  # Include static files
        "--hidden-import", "webview",
        "--hidden-import", "flaskwebgui",
        "--hidden-import", "flask",
        "--hidden-import", "flask_security",
        "--hidden-import", "flask_security.too",
        "--hidden-import", "flask_wtf",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "bcrypt",
        "--hidden-import", "pandas",
        "--hidden-import", "pyarrow",
        "--hidden-import", "jinja2",
        "--hidden-import", "werkzeug",
        "--collect-all", "flask",
        "--collect-all", "flask_security",
        "desktop_app.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def copy_to_distribution():
    """Copy the built executable and documentation to the distribution folder"""
    import shutil
    from datetime import datetime
    
    # Ensure distribution directory exists
    if not os.path.exists('distribution'):
        os.makedirs('distribution')
    
    # Determine executable name based on platform
    if sys.platform == 'win32':
        exe_name = 'ApeWellnessTracker.exe'
    elif sys.platform == 'darwin':
        exe_name = 'ApeWellnessTracker'
        # For macOS, we need to handle .app bundle
        app_bundle = 'dist/Ape Wellness Tracker.app'
        if os.path.exists(app_bundle):
            dest_bundle = 'distribution/Ape Wellness Tracker.app'
            if os.path.exists(dest_bundle):
                shutil.rmtree(dest_bundle)
            shutil.copytree(app_bundle, dest_bundle)
            print(f"Copied app bundle to: {dest_bundle}")
            return
    else:
        exe_name = 'ApeWellnessTracker'
    
    # Copy executable
    source = f'dist/{exe_name}'
    destination = f'distribution/{exe_name}'
    
    if os.path.exists(source):
        try:
            # Remove existing file if it exists
            if os.path.exists(destination):
                os.remove(destination)
            shutil.copy2(source, destination)
            print(f"Copied executable to: {destination}")
        except Exception as e:
            print(f"Warning: Could not copy executable: {e}")
    else:
        print(f"Warning: Source executable not found: {source}")
    
    # Copy researcher instructions if they exist
    if os.path.exists('distribution/RESEARCHER_INSTRUCTIONS.txt'):
        print("Researcher instructions already exist in distribution folder")
    else:
        # Create default researcher instructions if they don't exist
        create_researcher_instructions()
    
    # Update build date in researcher instructions
    update_build_date()

def create_researcher_instructions():
    """Create researcher-friendly instructions"""
    from datetime import datetime
    build_date = datetime.now().strftime("%Y-%m-%d")
    
    instructions = '''APE WELLNESS TRACKER - RESEARCHER INSTRUCTIONS
===============================================

A desktop application for tracking ape nutrition and wellness data.

QUICK START:
1. Double-click ApeWellnessTracker.exe
2. Register a new account (first time only)
3. Start tracking your apes' nutrition!

FEATURES:
- Add and manage ape profiles with photos
- Log feeding sessions and meals
- Track nutrition data and calories
- Generate comprehensive reports
- Export data in multiple formats (CSV, ZIP)
- User authentication and data security
- Archive inactive apes
- Recipe management system

SYSTEM REQUIREMENTS:
- Windows 10 or later (or macOS 10.13+)
- 200MB free disk space
- No internet connection required (runs locally)
- No Python installation needed

FIRST TIME SETUP:
1. Run ApeWellnessTracker.exe
2. Click "Register" to create your account
3. Login with your credentials
4. Start adding your apes and logging data

USING THE APPLICATION:
- Dashboard: Overview of all apes and recent activity
- Add Ape: Create new ape profiles with photos and details
- Log Meal: Record feeding sessions with recipes
- Reports: Generate nutrition and wellness reports
- Export: Download your data for analysis

DATA MANAGEMENT:
- All data is stored locally on your computer
- Data is automatically saved in the application
- You can export data anytime for external analysis
- Each user has their own separate data
- Database file location: Same folder as the executable

TROUBLESHOOTING:
- If the app doesn't start: Try running as administrator
- If you get security warnings: Allow the app through Windows Defender/Antivirus
- If the window is too small: Resize by dragging the corners
- If you lose your password: Contact the administrator
- If port 5003 is in use: Close other instances of the app

SUPPORT:
For technical support or questions, contact:
dylandaner@me.com
zmielko@highlands.edu

VERSION: 1.0.0
BUILD DATE: {build_date}

IMPORTANT NOTES:
- This application runs completely offline
- Your data is stored securely on your local machine
- No data is sent to external servers
- You can export your data at any time
- The application includes built-in help and documentation
- First launch may take 5-10 seconds (this is normal)
'''
    instructions = instructions.format(build_date=build_date)
    
    dist_file = 'distribution/RESEARCHER_INSTRUCTIONS.txt'
    with open(dist_file, 'w') as f:
        f.write(instructions)
    print(f"Created {dist_file}")

def update_build_date():
    """Update build date in researcher instructions"""
    from datetime import datetime
    build_date = datetime.now().strftime("%Y-%m-%d")
    
    instructions_file = 'distribution/RESEARCHER_INSTRUCTIONS.txt'
    if os.path.exists(instructions_file):
        with open(instructions_file, 'r') as f:
            content = f.read()
        
        # Update build date
        import re
        content = re.sub(r'BUILD DATE: .*', f'BUILD DATE: {build_date}', content)
        
        with open(instructions_file, 'w') as f:
            f.write(content)
        print(f"Updated build date in {instructions_file}")

def create_installer_script():
    """Create a simple installer script (for development only)"""
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
        
        # Copy executable to distribution folder
        copy_to_distribution()
        
        # Create installer script (for development)
        create_installer_script()
        
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print("\nDistribution package ready in 'distribution/' folder:")
        print("  - Executable: distribution/ApeWellnessTracker.exe")
        print("  - Instructions: distribution/RESEARCHER_INSTRUCTIONS.txt")
        print("\nTo distribute to researchers:")
        print("  1. Zip the entire 'distribution' folder")
        print("  2. Send the zip file to researchers")
        print("  3. Researchers extract and run ApeWellnessTracker.exe")
        print("\nNext steps:")
        print("  1. Test the executable: distribution/ApeWellnessTracker.exe")
        print("  2. Verify all features work correctly")
        print("  3. Create zip file for distribution")
    else:
        print("Build failed. Please check the error messages above.")

if __name__ == '__main__':
    main()
