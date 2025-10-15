# Ape Wellness Tracker - Distribution Guide

This guide explains how to package and distribute your desktop application to other users.

## Distribution Options

### Option 1: Standalone Executable (Recommended)
Create a single `.exe` file that users can run without installing Python.

### Option 2: Python Package
Distribute the source code with installation instructions.

### Option 3: Web Version
Deploy to a web server for browser access.

---

## Option 1: Standalone Executable

### Step 1: Build the Executable

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Build the executable
python build_desktop.py
```

This creates:
- `dist/ApeWellnessTracker.exe` - The standalone executable
- `install_desktop.bat` - Windows installer script

### Step 2: Test the Executable

```bash
# Test the built executable
dist/ApeWellnessTracker.exe
```

### Step 3: Package for Distribution

Create a distribution folder with:
```
ApeWellnessTracker/
├── ApeWellnessTracker.exe
├── README.txt
└── install_desktop.bat (optional)
```

### Step 4: Distribute

**Methods:**
- Email the folder as a ZIP file
- Upload to cloud storage (Google Drive, Dropbox, etc.)
- Create an installer using tools like Inno Setup
- Host on a website for download

---

## Option 2: Python Package Distribution

### Step 1: Create Installation Package

```bash
# Create a ZIP with source code
zip -r ape-wellness-tracker.zip . -x "*.pyc" "__pycache__/*" "*.git*" "venv/*" "dist/*" "build/*"
```

### Step 2: Include Installation Instructions

Create `INSTALLATION_INSTRUCTIONS.txt`:

```
APE WELLNESS TRACKER - INSTALLATION INSTRUCTIONS
================================================

REQUIREMENTS:
- Python 3.8 or higher
- Internet connection (for installing dependencies)

INSTALLATION STEPS:
1. Extract this ZIP file to a folder on your computer
2. Open Command Prompt/Terminal in that folder
3. Run: pip install -r requirements.txt
4. Run: python desktop_app.py

ALTERNATIVE (if you have Python):
1. Extract the ZIP file
2. Double-click: launch_desktop.py

TROUBLESHOOTING:
- If you get "Python not found": Install Python from python.org
- If you get "pip not found": Install pip or use: python -m pip install -r requirements.txt
- If the app doesn't start: Check the console output for error messages

SUPPORT:
Contact [your-email] for help
```

---

## Option 3: Web Deployment

### Deploy to Heroku (Free)

1. Create `Procfile`:
```
web: python run.py
```

2. Create `runtime.txt`:
```
python-3.11.0
```

3. Deploy:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
git push heroku main
```

### Deploy to PythonAnywhere (Free)

1. Upload your code to PythonAnywhere
2. Configure web app to use your Flask app
3. Set up static files mapping

---

## User Access Methods

### For Standalone Executable Users:
1. Download the ZIP file
2. Extract it
3. Double-click `ApeWellnessTracker.exe`
4. The app opens in a desktop window

### For Python Package Users:
1. Download the ZIP file
2. Extract it
3. Install Python (if not installed)
4. Run: `pip install -r requirements.txt`
5. Run: `python desktop_app.py`

### For Web Version Users:
1. Visit the URL you provide
2. Use in any web browser
3. No installation required

---

## Creating a Professional Installer

### Using Inno Setup (Windows)

1. Download Inno Setup
2. Create installer script:

```ini
[Setup]
AppName=Ape Wellness Tracker
AppVersion=1.0
DefaultDirName={pf}\ApeWellnessTracker
DefaultGroupName=Ape Wellness Tracker
OutputDir=installer
OutputBaseFilename=ApeWellnessTracker-Setup

[Files]
Source: "dist\ApeWellnessTracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Ape Wellness Tracker"; Filename: "{app}\ApeWellnessTracker.exe"
Name: "{commondesktop}\Ape Wellness Tracker"; Filename: "{app}\ApeWellnessTracker.exe"
```

3. Build the installer

---

## Testing Your Distribution

### Before Sending to Users:

1. **Test on a clean machine:**
   - Use a virtual machine
   - Or test on a different computer
   - Make sure Python isn't installed (for executable testing)

2. **Test all features:**
   - User registration/login
   - Adding apes
   - Logging meals
   - Viewing reports
   - All CRUD operations

3. **Test different scenarios:**
   - First-time user
   - User with existing data
   - Network connectivity issues
   - Different screen resolutions

---

## Quick Distribution Commands

### Build and Package Everything:

```bash
# Build executable
python build_desktop.py

# Create distribution ZIP
mkdir distribution
cp dist/ApeWellnessTracker.exe distribution/
cp README.txt distribution/
cp DESKTOP_README.md distribution/
zip -r ApeWellnessTracker-Distribution.zip distribution/

# Create source package
zip -r ApeWellnessTracker-Source.zip . -x "*.pyc" "__pycache__/*" "*.git*" "venv/*" "dist/*" "build/*" "instance/*"
```

---

## Support and Documentation

### Include with Distribution:

1. **README.txt** - Basic instructions
2. **DESKTOP_README.md** - Detailed documentation
3. **TROUBLESHOOTING.txt** - Common issues and solutions
4. **CONTACT.txt** - How to get help

### Example README.txt:

```
APE WELLNESS TRACKER
===================

A desktop application for tracking ape nutrition and wellness data.

QUICK START:
1. Double-click ApeWellnessTracker.exe
2. Register a new account or login
3. Start tracking your apes' nutrition!

FEATURES:
- Add and manage ape profiles
- Log feeding sessions
- Track nutrition data
- Generate reports
- Export data

SYSTEM REQUIREMENTS:
- Windows 10 or later
- 100MB free disk space
- Internet connection (for initial setup)

SUPPORT:
For help, contact: [your-email]
Documentation: See DESKTOP_README.md

VERSION: 1.0.0
```

This gives you multiple ways to distribute your app depending on your users' technical level and preferences!
