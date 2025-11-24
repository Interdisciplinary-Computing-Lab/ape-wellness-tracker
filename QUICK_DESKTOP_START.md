# Quick Start: Desktop Port

## ✅ Your Desktop Port is Ready!

Your application already has a fully functional desktop port. Here's how to use it:

## 🚀 Run Desktop App (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Desktop App
```bash
python desktop_app.py
```

That's it! A native desktop window will open with your Flask app running inside.

## 📦 Build Standalone Executable

### Windows
```cmd
build_windows.bat
```
Output: `dist\ApeWellnessTracker.exe`

### macOS
```bash
chmod +x build_mac.sh
./build_mac.sh
```
Output: `dist/Ape Wellness Tracker.app`

### Or Use Python Build Script
```bash
python build_desktop.py
```

## 🎯 How It Works

1. **Flask Server**: Runs on `localhost:5003` (background thread)
2. **Desktop Window**: Native window using `pywebview` 
3. **Integration**: Window loads Flask app from localhost

## 📁 Key Files

- `desktop_app.py` - Main desktop entry point
- `build_desktop.py` - PyInstaller build script
- `build_windows.bat` - Windows build script
- `build_mac.sh` - macOS build script

## 🔧 Customization

### Change Window Size
Edit `desktop_app.py` line 44-45:
```python
width=1400,   # Change this
height=900,   # Change this
```

### Debug Mode
```bash
python desktop_app.py --debug
```

## ❓ Troubleshooting

**"pywebview not available"**
```bash
pip install pywebview
```

**"Port 5003 in use"**
- Close other instances
- Or change port in `desktop_app.py` line 29

**Build fails?**
```bash
pip install --upgrade pyinstaller
```

## 📚 More Info

- See `DESKTOP_PORT_GUIDE.md` for complete documentation
- See `DESKTOP_BUILD.md` for detailed build instructions
- See `DESKTOP_README.md` for user documentation

