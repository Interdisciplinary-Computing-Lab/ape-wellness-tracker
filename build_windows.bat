@echo off
REM Build script for Windows desktop application
REM This script creates a standalone Windows .exe using PyInstaller

echo Building Windows Desktop Application...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed.
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "Ape Wellness Tracker.spec" del /q "Ape Wellness Tracker.spec"

REM Create the spec file for PyInstaller
echo Creating PyInstaller spec file...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['desktop_app.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('backend/templates', 'backend/templates'),
echo         ('backend/static', 'backend/static'),
echo     ],
echo     hiddenimports=[
echo         'webview',
echo         'flask',
echo         'flask_security',
echo         'flask_wtf',
echo         'sqlalchemy',
echo         'bcrypt',
echo         'pandas',
echo         'pyarrow',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='Ape Wellness Tracker',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon=None,
echo ^)
) > ape_wellness_tracker.spec

REM Build the application
echo Building application with PyInstaller...
pyinstaller --clean ape_wellness_tracker.spec

REM Check if build was successful
if exist "dist\Ape Wellness Tracker.exe" (
    echo.
    echo Build successful!
    echo.
    echo Application created at: dist\Ape Wellness Tracker.exe
    echo.
    echo To test the application, run:
    echo   dist\Ape Wellness Tracker.exe
) else (
    echo Build failed. Check the output above for errors.
    exit /b 1
)

pause

