@echo off
echo Installing Ape Wellness Tracker Desktop App...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create desktop shortcut (Windows)
if exist "%USERPROFILE%\Desktop" (
    echo Creating desktop shortcut...
    echo [InternetShortcut] > "%USERPROFILE%\Desktop\Ape Wellness Tracker.url"
    echo URL=file:///%CD%\launch_desktop.py >> "%USERPROFILE%\Desktop\Ape Wellness Tracker.url"
)

echo.
echo Installation complete!
echo You can now run the application using launch_desktop.py
pause
