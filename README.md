# Ape Diet & Wellness Tracker

A Flask-based web application for tracking diet and wellness data for apes at Ape Initiative. Built with Flask, Bootstrap, Chart.js, and SQLite.

## Getting Started

You'll need Python 3.7 or higher and pip installed. Once you have that:

1. Clone the repository and navigate to the project directory
2. Install the dependencies: `pip install -r requirements.txt`
3. Run the app: `python run.py`

The app will start on `http://localhost:5003`. The database gets created automatically in the `instance/` folder the first time you run it, but you can also initialize it manually with `python scripts/init_db.py` if needed.

After starting the app, you might want to create an admin user with `python scripts/create_admin.py`, or create a regular user with `python scripts/create_user.py`. If you want some sample data to work with, run `python scripts/seed_data.py`.

## Running as a Desktop App

You can run the app in a desktop window instead of a browser by using `python desktop_app.py`. This wraps the Flask app in a native window using pywebview.

To build a standalone desktop application:

**On macOS:**
- Make sure PyInstaller is installed: `pip install pyinstaller`
- Run the build script: `./build_scripts/build_mac.sh`
- The app bundle will be in `dist/Ape Wellness Tracker.app`

You can also create a DMG file for distribution:
```bash
hdiutil create -volname "Ape Wellness Tracker" \
  -srcfolder "dist/Ape Wellness Tracker.app" \
  -ov -format UDZO "dist/Ape Wellness Tracker.dmg"
```

**On Windows:**
- Install PyInstaller: `pip install pyinstaller`
- Run the build script: `.\build_scripts\build_windows.bat`
- The executable will be at `dist\Ape Wellness Tracker.exe`

The desktop versions are standalone executables that don't require Python to be installed on the end user's machine. Everything is bundled together, including the database which gets stored locally in the app's instance folder.

## Project Structure

The Flask app code lives in the `backend/` folder. Routes, templates, static files, models, and forms are all organized there. The database and other instance-specific files go in `instance/`, which gets created automatically when you first run the app.

Utility scripts are in `scripts/`, build scripts for packaging the desktop app are in `build_scripts/`, and configuration files are in `config/`. The main entry point is `run.py`, and `desktop_app.py` is what you use to run it as a desktop application.
