#!/bin/bash
# Build script for macOS desktop application
# This script creates a standalone macOS .app bundle using PyInstaller

set -e  # Exit on error

echo "🍎 Building macOS Desktop Application..."
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller is not installed."
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This script is designed for macOS."
    echo "You're running on: $OSTYPE"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec
rm -rf "Ape Wellness Tracker.app"

# Create the spec file for PyInstaller
echo "📝 Creating PyInstaller spec file..."
cat > ape_wellness_tracker.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend', 'backend'),
        ('backend/templates', 'backend/templates'),
        ('backend/static', 'backend/static'),
    ],
    hiddenimports=[
        'webview',
        'flask',
        'flask_sqlalchemy',
        'flask_sqlalchemy._compat',
        'flask_security',
        'flask_security.too',
        'flask_security.utils',
        'flask_security.datastore',
        'flask_wtf',
        'flask_wtf.csrf',
        'sqlalchemy',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        'sqlalchemy.sql',
        'bcrypt',
        'pandas',
        'pyarrow',
        'pyarrow.lib',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.security',
        'werkzeug.utils',
        'flaskwebgui',
        'openpyxl',
        'blinker',
        'click',
        'itsdangerous',
        'markupsafe',
        'passlib',
        'passlib.handlers',
        'passlib.handlers.bcrypt',
        'passlib.handlers.argon2',
        'passlib.handlers.pbkdf2',
        'passlib.handlers.sha2_crypt',
        'passlib.handlers.django',
        'passlib.context',
        'passlib.registry',
        'passlib.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    collect_all=['passlib'],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Use onedir mode for better macOS performance
    name='Ape Wellness Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Ape Wellness Tracker',
)

app = BUNDLE(
    coll,
    name='Ape Wellness Tracker.app',
    icon=None,  # Add icon path here if you have one
    bundle_identifier='com.apeinitiative.wellnesstracker',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Ape Wellness Tracker',
        'CFBundleDisplayName': 'Ape Wellness Tracker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSMinimumSystemVersion': '10.13.0',
    },
)
EOF

# Build the application
echo "🔨 Building application with PyInstaller..."
pyinstaller --clean ape_wellness_tracker.spec

# Check if build was successful
if [ -d "dist/Ape Wellness Tracker.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📦 Application bundle created at: dist/Ape Wellness Tracker.app"
    echo ""
    echo "To test the application, run:"
    echo "  open 'dist/Ape Wellness Tracker.app'"
    echo ""
    echo "To create a DMG installer, you can use:"
    echo "  hdiutil create -volname 'Ape Wellness Tracker' -srcfolder 'dist/Ape Wellness Tracker.app' -ov -format UDZO 'dist/Ape Wellness Tracker.dmg'"
else
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi

