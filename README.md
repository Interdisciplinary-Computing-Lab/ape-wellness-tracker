# Ape Diet & Wellness Tracker App
A full-stack diet and wellness tracking app for Ape Initiative, built with Flask, HTML5, Bootstrap 4, Chart.js, and SQLite.

## 🔧 Project Status

✅ Core Backend and Authentication Implemented  
✅ Frontend Integration and Styling Completed  
✅ Prototype Ready - Professional UI/UX  

🚧 Production Configuration Needed  
📌 Deployment Setup and Final Testing Pending

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ape-wellness-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   The database will be automatically created in the `instance/` folder when you first run the app. However, if you want to explicitly initialize it:
   ```bash
   python scripts/init_db.py
   ```

4. **Run the application**
   ```bash
   python run.py
   ```
   
   The app will be available at `http://localhost:5003`

### First Time Setup

After starting the app for the first time, you may want to:
- Create an admin user: `python scripts/create_admin.py`
- Create a test user: `python scripts/create_user.py`
- Seed sample data: `python scripts/seed_data.py`

## 💻 Desktop Application

The app can be packaged as a standalone desktop application for both macOS and Windows.

### Running as Desktop App (Development)

To run the app in a desktop window during development:

```bash
python desktop_app.py
```

This will launch the Flask app in a native desktop window using pywebview.

### Building Standalone Desktop Applications

#### macOS

1. **Install build dependencies:**
   ```bash
   pip install pyinstaller
   ```

2. **Run the build script:**
   ```bash
   ./build_scripts/build_mac.sh
   ```

3. **The application bundle will be created at:**
   ```
   dist/Ape Wellness Tracker.app
   ```

4. **To test the app:**
   ```bash
   open "dist/Ape Wellness Tracker.app"
   ```

5. **Optional: Create a DMG installer:**
   ```bash
   hdiutil create -volname "Ape Wellness Tracker" \
     -srcfolder "dist/Ape Wellness Tracker.app" \
     -ov -format UDZO "dist/Ape Wellness Tracker.dmg"
   ```

#### Windows

1. **Install build dependencies:**
   ```powershell
   pip install pyinstaller
   ```

2. **Run the build script:**
   ```powershell
   .\build_scripts\build_windows.bat
   ```

3. **The executable will be created at:**
   ```
   dist\Ape Wellness Tracker.exe
   ```

### Desktop App Features

- ✅ Native window (no browser required)
- ✅ Cross-platform (macOS and Windows)
- ✅ Standalone executable (no Python installation needed for end users)
- ✅ All dependencies bundled
- ✅ Database stored locally in the app's instance folder

## 🗂 Project Structure

This app uses Flask to serve both backend logic and frontend UI. All app code lives inside the `backend/` folder, while the database and configuration files live in the `instance/` folder.
```
ape-wellness-tracker/
├── backend/                 # Flask app logic and structure
│   ├── __init__.py          # App factory that initializes Flask
│   ├── routes/              # Flask route handlers (views)
│   ├── templates/           # HTML templates rendered by Flask
│   ├── static/              # CSS, JS, and image assets
│   ├── models/              # Database models
│   └── forms/               # Form classes using Flask-WTF
│
├── scripts/                 # Utility and management scripts
│   ├── init_db.py           # Database initialization
│   ├── create_admin.py      # Create admin users
│   ├── seed_data.py         # Seed sample data
│   └── migrate_*.py         # Database migration scripts
│
├── build_scripts/           # Build and packaging scripts
│   ├── build_desktop.py     # PyInstaller build script
│   ├── build_mac.sh         # macOS build script
│   ├── build_windows.bat    # Windows build script
│   └── package_*.py         # Distribution packaging scripts
│
├── config/                  # Configuration files
│   └── export_config.py     # Export system configuration
│
├── docs/                    # Documentation files
│   ├── DESKTOP_BUILD.md     # Desktop build instructions
│   └── *.md                 # Additional documentation
│
├── tests/                   # Test files
│
├── instance/                # Instance-specific files (created automatically)
│   └── database.db          # SQLite database file
│
├── run.py                   # Main entry point to start the Flask app
├── desktop_app.py           # Desktop application entry point (pywebview)
├── launch_desktop.py        # Desktop app launcher
├── requirements.txt         # Python dependencies
└── LICENSE                  # License file
