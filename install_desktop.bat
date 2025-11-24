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

echo.
echo Installation complete!
echo You can now run the application using launch_desktop.py
pause
