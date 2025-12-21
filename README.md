# Ape Diet & Wellness Tracker

A Flask-based web application for tracking diet and wellness data for apes at Ape Initiative.

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python run.py`
3. Access at `http://localhost:5003`

The database is created automatically in `instance/` on first run. Create an admin user with `python misc/scripts/create_admin.py` after starting the app.

## Desktop App

Run in desktop mode: `python desktop_app.py`

To build standalone executables:
- **macOS:** `./build_scripts/build_mac.sh` → `dist/Ape_Meal_Tracker.app`
- **Windows:** `.\build_scripts\build_windows.bat` → `dist\Ape Wellness Tracker.exe`
