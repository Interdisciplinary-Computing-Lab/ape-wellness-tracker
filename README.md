# Ape Diet & Wellness Tracker

A Flask-based web application for tracking dietary meals for bonobo apes at Ape Initiative.

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. (Recommended) Copy `.env.example` to `.env` and run `python misc/scripts/generate_secrets.py` to fill in `SECRET_KEY` and `SECURITY_PASSWORD_SALT`
3. Run the app: `python run.py`
4. Access at `http://localhost:5003`

The database is created automatically in `instance/` on first run.

**Login / register issues:** If passwords stop working after a restart, the app may have rotated secrets. Either set stable values in `.env`, or reset a password:

```powershell
python misc/scripts/reset_password.py your@email.com YourNewPassword
```

Create an admin user with `python misc/scripts/create_admin.py` after starting the app (default: `admin@apeinitiative.org` / `admin123` if no users exist).

## USDA nutrition data (optional)

For accurate food sources, download **USDA FoodData Central – Foundation Foods** CSV (not FDA bulk data) and extract into `data/fdc/raw/`. See [data/fdc/README.md](data/fdc/README.md) for download links and layout. Raw CSV/zips are gitignored; only the README and folder structure are committed.

## Desktop App

Run in desktop mode: `python desktop_app.py`

To build standalone executables:
- **macOS:** `./build_scripts/build_mac.sh` → `dist/Ape_Meal_Tracker.app`
- **Windows:** `.\build_scripts\build_windows.bat` → `dist\Ape Wellness Tracker.exe`
