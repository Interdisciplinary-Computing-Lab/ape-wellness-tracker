# Desktop Port Guide - Ape Wellness Tracker

## Overview

Your application already has a fully functional desktop port! This guide explains how it works and how to use it.

## Architecture

The desktop port uses a **hybrid architecture**:

1. **Flask Backend**: Your existing Flask web application runs on `localhost:5003`
2. **Desktop Window**: A native desktop window wraps the Flask app using one of two methods:
   - **Primary**: `pywebview` - Lightweight, native webview wrapper
   - **Fallback**: `flaskwebgui` - Alternative desktop wrapper

### How It Works

```
┌─────────────────────────────────────┐
│   Desktop Window (pywebview)        │
│  ┌───────────────────────────────┐  │
│  │  Flask App (localhost:5003)   │  │
│  │  - All your routes            │  │
│  │  - Templates & Static files   │  │
│  │  - Database (SQLite)          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Quick Start

### Option 1: Run from Source (Development)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the desktop app**:
   ```bash
   python desktop_app.py
   ```

   Or use the launcher:
   ```bash
   python launch_desktop.py
   ```

### Option 2: Build Standalone Executable

#### Windows

```cmd
build_windows.bat
```

Or manually:
```cmd
python build_desktop.py
```

Output: `dist\ApeWellnessTracker.exe`

#### macOS

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Output: `dist/Ape Wellness Tracker.app`

#### Linux

```bash
python build_desktop.py
```

## File Structure

```
├── desktop_app.py          # Main desktop application entry point
├── launch_desktop.py       # Simple launcher with dependency checking
├── build_desktop.py        # PyInstaller build script
├── build_windows.bat       # Windows-specific build script
├── build_mac.sh            # macOS-specific build script
├── ApeWellnessTracker.spec # PyInstaller spec file
└── distribution/           # Distribution folder for built executables
```

## How the Desktop Port Works

### 1. Desktop App Entry Point (`desktop_app.py`)

The main file does the following:

1. **Creates Flask app**: Uses your existing `create_app()` function
2. **Starts Flask server**: Runs Flask on `127.0.0.1:5003` in a background thread
3. **Opens desktop window**: Uses `pywebview` to create a native window
4. **Loads Flask app**: The window navigates to `http://127.0.0.1:5003`

### 2. Key Features

- ✅ **Native window**: Looks like a desktop app, not a browser
- ✅ **Automatic server management**: Flask starts/stops automatically
- ✅ **Cross-platform**: Works on Windows, macOS, and Linux
- ✅ **Standalone executable**: Can be packaged as a single `.exe` or `.app`
- ✅ **Fallback support**: Falls back to `flaskwebgui` if `pywebview` fails

### 3. Port Configuration

- **Default port**: `5003`
- **Host**: `127.0.0.1` (localhost only - secure)
- **Why localhost?**: The app is only accessible on the local machine, not over the network

## Building for Distribution

### Step-by-Step Build Process

1. **Install build dependencies**:
   ```bash
   pip install pyinstaller
   ```

2. **Run build script**:
   ```bash
   python build_desktop.py
   ```

3. **Test the executable**:
   - Windows: `dist\ApeWellnessTracker.exe`
   - macOS: `dist/Ape Wellness Tracker.app`

4. **Distribute**:
   - Copy the entire `distribution/` folder
   - Or create an installer (see below)

### What Gets Packaged

PyInstaller bundles:
- ✅ Python interpreter
- ✅ All Python dependencies
- ✅ Your Flask application code
- ✅ Templates (`backend/templates/`)
- ✅ Static files (`backend/static/`)
- ✅ Database will be created in the app's directory

### File Size

- **Typical size**: 100-200 MB
- **Why so large?**: Includes Python + all dependencies
- **This is normal**: All standalone Python apps are this size

## Customization

### Change Window Size

Edit `desktop_app.py`:

```python
window = webview.create_window(
    "Ape Wellness Tracker",
    "http://127.0.0.1:5003",
    width=1600,      # Change this
    height=1000,     # Change this
    min_size=(1024, 768),
    ...
)
```

### Add Application Icon

1. **Create icon files**:
   - Windows: `.ico` file
   - macOS: `.icns` file

2. **Update build script**:
   - Windows: Add `--icon=icon.ico` to PyInstaller command
   - macOS: Add `icon='icon.icns'` to BUNDLE in spec file

### Change App Name

1. Update `desktop_app.py`:
   ```python
   window = webview.create_window(
       "Your Custom Name",  # Change here
       ...
   )
   ```

2. Update spec file:
   ```python
   name='Your Custom Name',
   ```

## Troubleshooting

### Issue: "pywebview not available"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Port 5003 already in use"

**Solution**: 
1. Close any other instances of the app
2. Or modify `desktop_app.py` to use a different port

### Issue: Desktop window doesn't open

**Solution**: 
- The app will fallback to `flaskwebgui`
- Check console output for error messages
- Try running `python run.py` to test Flask separately

### Issue: Build fails

**Common causes**:
1. Missing dependencies - Run `pip install -r requirements.txt`
2. Missing files - Ensure `backend/templates/` and `backend/static/` exist
3. PyInstaller issues - Try: `pip install --upgrade pyinstaller`

### Issue: Executable is large

**This is normal!** PyInstaller bundles:
- Python interpreter (~30-50 MB)
- All dependencies (~50-100 MB)
- Your application code

Total: 100-200 MB is expected.

### Issue: Antivirus flags the .exe

**Solution**: 
- This is a known PyInstaller issue
- Code-sign the executable (requires certificate)
- Or whitelist in antivirus

## Advanced: Using Electron Instead

If you want to use Electron instead of pywebview:

1. **Install Electron**:
   ```bash
   npm install electron --save-dev
   ```

2. **Create Electron wrapper**:
   - Main process: Starts Flask server
   - Renderer process: Loads Flask app in Electron window

3. **Benefits of Electron**:
   - More control over window behavior
   - Better developer tools
   - More customization options

4. **Drawbacks**:
   - Larger file size (~150-200 MB)
   - More complex setup
   - Requires Node.js

## Testing Checklist

Before distributing, test:

- [ ] App launches successfully
- [ ] Login/Registration works
- [ ] All CRUD operations work
- [ ] Database persists after closing
- [ ] Window resizing works
- [ ] No console errors
- [ ] Works on clean system (without Python installed)

## Distribution

### Windows

1. **Distribute as .exe**:
   - Share `ApeWellnessTracker.exe`
   - Users double-click to run

2. **Create installer** (optional):
   - Use Inno Setup or NSIS
   - Creates professional installer

### macOS

1. **Distribute as .app**:
   - Share `Ape Wellness Tracker.app`
   - Users drag to Applications folder

2. **Create DMG** (optional):
   ```bash
   hdiutil create -volname "Ape Wellness Tracker" \
     -srcfolder "dist/Ape Wellness Tracker.app" \
     -ov -format UDZO "Ape Wellness Tracker.dmg"
   ```

### Code Signing (Optional)

For production distribution:
- **Windows**: Code-sign with Authenticode certificate
- **macOS**: Code-sign with Apple Developer certificate

## Performance Tips

1. **First launch is slower**: Files are extracted
2. **Subsequent launches**: Much faster
3. **Memory usage**: ~100-200 MB (normal for Flask apps)
4. **Startup time**: 2-5 seconds

## Security Notes

- ✅ App runs on localhost only (127.0.0.1)
- ✅ No external network access
- ✅ Database is local to the application
- ✅ All Flask-Security features preserved

## Next Steps

1. **Test the desktop app**: `python desktop_app.py`
2. **Build executable**: `python build_desktop.py`
3. **Test on clean system**: Ensure it works without Python installed
4. **Customize**: Add icon, change window size, etc.
5. **Distribute**: Share with users

## Support

- Check `DESKTOP_BUILD.md` for detailed build instructions
- Check `DESKTOP_README.md` for user-facing documentation
- PyInstaller docs: https://pyinstaller.org/
- pywebview docs: https://pywebview.flowrl.com/

