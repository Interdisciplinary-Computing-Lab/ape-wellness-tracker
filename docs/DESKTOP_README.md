# Ape Wellness Tracker - Desktop Port

This directory contains the desktop application version of the Ape Wellness Tracker, which wraps the Flask web application in a native desktop window using FlaskWebGUI.

## Features

- **Native Desktop Window**: Runs in a native desktop application window
- **Automatic Server Management**: Automatically starts and manages the Flask server
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Standalone Executable**: Can be packaged as a single executable file
- **Fallback Support**: Falls back to system browser if desktop window fails

## Quick Start

### Option 1: Run from Source

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch the desktop app:
   ```bash
   python launch_desktop.py
   ```

### Option 2: Run Directly

```bash
python desktop_app.py
```

### Option 3: Build Standalone Executable

1. Build the executable:
   ```bash
   python build_desktop.py
   ```

2. Run the executable:
   ```bash
   dist/ApeWellnessTracker.exe
   ```

## Files Overview

- `desktop_app.py` - Main desktop application wrapper
- `launch_desktop.py` - Simple launcher with dependency checking
- `build_desktop.py` - Build script for creating standalone executable
- `install_desktop.bat` - Windows installer script (created by build script)

## Technical Details

### Architecture

The desktop app uses a multi-threaded architecture:

1. **FlaskWebGUI**: Handles both the Flask server and desktop window
2. **Automatic Management**: No need for manual server management
3. **Built-in Browser**: Uses system browser engine for rendering

### Dependencies

- `flaskwebgui` - Desktop wrapper specifically designed for Flask applications
- `pyinstaller` - For creating standalone executables
- All existing Flask dependencies

### Port Configuration

- Default port: 5003
- Fallback port: 5004 (if 5003 is busy)
- Host: 127.0.0.1 (localhost only)

## Building for Distribution

### Windows

```bash
python build_desktop.py
```

This creates:
- `dist/ApeWellnessTracker.exe` - Standalone executable
- `install_desktop.bat` - Installation script

### macOS

```bash
python build_desktop.py
```

### Linux

```bash
python build_desktop.py
```

## Troubleshooting

### Common Issues

1. **"Missing required dependencies"**
   - Run: `pip install -r requirements.txt`

2. **"Failed to start Flask server"**
   - Check if port 5003 is available
   - Try running: `python run.py` to test Flask server separately

3. **Desktop window doesn't open**
   - The app will fallback to opening in your system browser
   - Check console output for error messages

4. **Build fails**
   - Ensure PyInstaller is installed: `pip install pyinstaller`
   - Check that all dependencies are installed

### Debug Mode

To run with debug output:

```bash
python desktop_app.py
```

Look for console output showing:
- Server startup messages
- Port information
- Error messages

## Development

### Adding Features

To extend the desktop app:

1. Modify `desktop_app.py` for core functionality
2. Update `build_desktop.py` for new dependencies
3. Test with `launch_desktop.py`

### Testing

1. Test Flask server separately:
   ```bash
   python run.py
   ```

2. Test desktop wrapper:
   ```bash
   python desktop_app.py
   ```

3. Test built executable:
   ```bash
   dist/ApeWellnessTracker.exe
   ```

## Security Notes

- The desktop app runs the Flask server on localhost only (127.0.0.1)
- No external network access by default
- Database remains local to the application
- All existing Flask-Security features are preserved

## Performance

- Desktop app adds minimal overhead (~10-20MB RAM)
- Startup time: ~2-3 seconds
- Window responsiveness: Native performance
- Server performance: Identical to web version
