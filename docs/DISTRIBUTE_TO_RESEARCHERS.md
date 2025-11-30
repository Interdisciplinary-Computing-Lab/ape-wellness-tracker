# Distributing Desktop App to Researchers

This guide explains how to build and package the desktop application for distribution to researchers.

## Quick Steps

### 1. Build the Executable

```bash
python build_desktop.py
```

This will:
- Clean previous builds
- Create a standalone executable using PyInstaller
- Copy the executable to the `distribution/` folder
- Create researcher instructions

### 2. Package for Distribution

```bash
python package_for_researchers.py
```

This creates a zip file: `ApeWellnessTracker-Desktop-v1.0-YYYYMMDD.zip`

### 3. Test Before Sending

1. Extract the zip file to a test folder
2. Run `ApeWellnessTracker.exe` from the extracted folder
3. Test:
   - Registration
   - Login
   - Adding an ape
   - Logging a meal
   - Generating reports
   - Exporting data

### 4. Send to Researchers

Send the zip file via:
- Email (if under size limit)
- Cloud storage (Google Drive, Dropbox, etc.)
- USB drive
- Network share

## What Researchers Receive

The zip file contains:
- `ApeWellnessTracker.exe` - The application (standalone, no installation needed)
- `RESEARCHER_INSTRUCTIONS.txt` - Detailed instructions
- `README.txt` - Quick start guide

## System Requirements for Researchers

- **Windows**: Windows 10 or later (64-bit)
- **macOS**: macOS 10.13 (High Sierra) or later
- **Disk Space**: 200MB free
- **No Internet**: Application runs completely offline
- **No Python**: No additional software installation needed

## Building for Different Platforms

### Windows (Current System)

```bash
python build_desktop.py
```

Output: `distribution/ApeWellnessTracker.exe`

### macOS

On a Mac, run:
```bash
./build_mac.sh
```

Output: `distribution/Ape Wellness Tracker.app`

Then create a DMG:
```bash
cd distribution
hdiutil create -volname "Ape Wellness Tracker" \
  -srcfolder "Ape Wellness Tracker.app" \
  -ov -format UDZO "ApeWellnessTracker-macOS.dmg"
```

## File Sizes

- **Executable**: ~100-200 MB (includes Python + all dependencies)
- **Zip file**: ~80-150 MB (compressed)
- **This is normal**: All standalone Python apps are this size

## Troubleshooting Build Issues

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Missing modules" error
```bash
pip install -r requirements.txt
```

### Build fails with import errors
- Check that all dependencies are in `requirements.txt`
- Add missing imports to `--hidden-import` in `build_desktop.py`

### Executable is very large
- This is normal (100-200 MB)
- PyInstaller bundles Python + all dependencies
- Consider using `--onedir` instead of `--onefile` for smaller size (but multiple files)

## Testing Checklist

Before sending to researchers, test:

- [ ] Application launches successfully
- [ ] Registration works
- [ ] Login works
- [ ] Can add an ape
- [ ] Can upload ape photo
- [ ] Can log a meal
- [ ] Can view reports
- [ ] Can export data (CSV, ZIP)
- [ ] Database persists after closing
- [ ] Window resizing works
- [ ] No console errors
- [ ] Works on clean Windows system (no Python installed)

## Distribution Methods

### Option 1: Email (Small Groups)
- Attach zip file if under email size limit (usually 25MB)
- For larger files, use cloud storage

### Option 2: Cloud Storage
- Upload to Google Drive, Dropbox, OneDrive
- Share download link with researchers
- Set appropriate permissions

### Option 3: USB Drive
- Copy zip file to USB drive
- Include printed instructions if needed

### Option 4: Network Share
- Place zip file on shared network drive
- Provide researchers with network path

## Security Considerations

### Code Signing (Optional but Recommended)

For production distribution, consider code signing:

**Windows:**
- Obtain a code signing certificate
- Sign the .exe to avoid Windows Defender warnings
- Tools: `signtool.exe` (Windows SDK)

**macOS:**
- Apple Developer account required
- Code sign and notarize the .app bundle
- Prevents "app is damaged" warnings

### Antivirus False Positives

- PyInstaller executables sometimes trigger antivirus warnings
- This is a known issue with packed executables
- Researchers may need to whitelist the application
- Code signing helps reduce false positives

## Version Management

### Updating the Version

1. Update version in `distribution/RESEARCHER_INSTRUCTIONS.txt`
2. Update version in this file
3. Rebuild: `python build_desktop.py`
4. Repackage: `python package_for_researchers.py`

### Version Numbering

Use semantic versioning:
- Major.Minor.Patch (e.g., 1.0.0)
- Increment patch for bug fixes
- Increment minor for new features
- Increment major for breaking changes

## Support for Researchers

### Common Questions

**Q: "Windows says the app is unsafe"**
A: This is normal for unsigned apps. Click "More info" then "Run anyway".

**Q: "The app won't start"**
A: Try running as administrator. Make sure no other instance is running.

**Q: "Where is my data stored?"**
A: In the same folder as the executable, in a subfolder called `instance/`.

**Q: "Can I move the app to another computer?"**
A: Yes, but copy the entire folder including the `instance/` subfolder to keep your data.

**Q: "How do I backup my data?"**
A: Use the Export feature in the app, or copy the `instance/` folder.

### Contact Information

Include in distribution:
- Technical support email: dylandaner@me.com
- Technical support email: zmielko@highlands.edu

## Advanced: Creating an Installer

For a more professional distribution, consider creating an installer:

### Windows: Inno Setup
1. Download Inno Setup (free)
2. Create installer script
3. Include: executable, instructions, shortcuts
4. Output: Professional installer (.exe)

### macOS: DMG with Installer
1. Create .app bundle (already done)
2. Create DMG with drag-to-Applications
3. Include README in DMG
4. Output: Professional DMG file

## Summary

**To create a distribution package:**

1. `python build_desktop.py` - Build executable
2. `python package_for_researchers.py` - Create zip file
3. Test the zip file
4. Send to researchers

**What researchers need to do:**

1. Extract zip file
2. Double-click `ApeWellnessTracker.exe`
3. Register account
4. Start using!

That's it! The application is completely standalone and requires no installation.

