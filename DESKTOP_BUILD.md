# Desktop Application Build Guide

This guide provides detailed instructions for building standalone desktop applications for macOS and Windows.

## Prerequisites

### For Both Platforms
- Python 3.7 or higher
- All dependencies from `requirements.txt` installed
- PyInstaller (will be installed automatically by build scripts)

### macOS Specific
- macOS 10.13 (High Sierra) or later
- Xcode Command Line Tools (install with: `xcode-select --install`)
- For code signing (optional): Apple Developer account

### Windows Specific
- Windows 7 or later
- Microsoft Visual C++ Redistributable (usually pre-installed)

## Quick Start

### Development Mode (Test Desktop App)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the desktop app:
   ```bash
   python desktop_app.py
   ```

   This will open a native window with the Flask app running inside.

### Building for Distribution

#### macOS

```bash
# Make script executable (if not already)
chmod +x build_mac.sh

# Run the build
./build_mac.sh
```

The build script will:
- Clean previous builds
- Create a PyInstaller spec file
- Build the `.app` bundle
- Output to `dist/Ape Wellness Tracker.app`

**Creating a DMG Installer:**
```bash
cd dist
hdiutil create -volname "Ape Wellness Tracker" \
  -srcfolder "Ape Wellness Tracker.app" \
  -ov -format UDZO "Ape Wellness Tracker.dmg"
```

#### Windows

```cmd
REM Run the build script
build_windows.bat
```

The build script will:
- Clean previous builds
- Create a PyInstaller spec file
- Build the `.exe` file
- Output to `dist\Ape Wellness Tracker.exe`

## Troubleshooting

### macOS Issues

**"pywebview requires a GUI framework"**
- Make sure you're running on macOS (not SSH)
- Install Cocoa support: The build script handles this automatically

**App won't open / "App is damaged"**
- This is a Gatekeeper security warning
- Right-click the app → Open (first time only)
- Or: `xattr -cr "dist/Ape Wellness Tracker.app"`

**Code Signing (for distribution outside App Store)**
- You'll need an Apple Developer account ($99/year)
- Or distribute without signing (users will need to allow it in Security settings)

### Windows Issues

**"Failed to execute script"**
- Make sure all dependencies are installed
- Check that `backend/templates` and `backend/static` folders exist
- Try building with `--debug` flag: `pyinstaller --debug all ape_wellness_tracker.spec`

**Antivirus false positives**
- Some antivirus software may flag PyInstaller executables
- This is a known issue - you may need to whitelist or code-sign the executable

### General Issues

**Large file size**
- PyInstaller bundles Python and all dependencies
- Typical size: 100-200 MB
- This is normal for standalone Python applications

**Slow startup time**
- First launch may be slower as files are extracted
- Subsequent launches are faster

**Database location**
- The database is stored in the app's instance folder
- On macOS: Inside the `.app` bundle
- On Windows: Next to the `.exe` file
- Users should not need to access this directly

## Customization

### Adding an Icon

**macOS:**
1. Create an `.icns` file (use `iconutil` or online converters)
2. Update `ape_wellness_tracker.spec`:
   ```python
   app = BUNDLE(
       exe,
       name='Ape Wellness Tracker.app',
       icon='path/to/icon.icns',  # Add this line
       ...
   )
   ```

**Windows:**
1. Create an `.ico` file
2. Update `ape_wellness_tracker.spec`:
   ```python
   exe = EXE(
       ...
       icon='path/to/icon.ico',  # Add this line
   )
   ```

### Changing Window Size

Edit `desktop_app.py`:
```python
webview.create_window(
    app_name,
    'http://127.0.0.1:5003',
    width=1600,  # Change width
    height=1000,  # Change height
    ...
)
```

### Changing App Name

1. Update `desktop_app.py`:
   ```python
   app_name = "Your Custom Name"
   ```

2. Update the spec file:
   - Change `name='Ape Wellness Tracker'` to your name
   - Change `name='Ape Wellness Tracker.app'` to `YourName.app`
   - Update `bundle_identifier` in the spec file

## Distribution

### macOS
- Distribute as `.app` bundle (users can drag to Applications)
- Or create a `.dmg` for easier installation
- Consider notarization for macOS 10.15+ (requires Apple Developer account)

### Windows
- Distribute as `.exe` file
- Consider code signing to avoid antivirus warnings
- You may want to create an installer using tools like Inno Setup or NSIS

## Testing

Before distributing, test the built application:

1. **Test on a clean system** (without Python/Flask installed)
2. **Test all features:**
   - Login/Registration
   - Creating apes
   - Logging feedings
   - Viewing reports
   - All CRUD operations

3. **Test database persistence:**
   - Close and reopen the app
   - Verify data is saved

4. **Test on different OS versions:**
   - macOS: Test on different macOS versions if possible
   - Windows: Test on Windows 10 and Windows 11

## Support

For issues or questions:
- Check the main README.md
- Review PyInstaller documentation: https://pyinstaller.org/
- Review pywebview documentation: https://pywebview.flowrl.com/

