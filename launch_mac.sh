#!/bin/bash
# Mac-specific launcher script for Ape Wellness Tracker Desktop App
# This script handles Mac-specific setup and launches the desktop app

set -e  # Exit on error

echo "Ape Wellness Tracker - Mac Desktop Launcher"
echo "=============================================="
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is designed for macOS only."
    echo "You're running on: $OSTYPE"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if desktop_app.py exists
if [ ! -f "desktop_app.py" ]; then
    echo "Error: desktop_app.py not found."
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.7 or later from python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check and install dependencies
echo "Checking dependencies..."
if ! python3 -c "import webview" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt --quiet
else
    echo "Dependencies are installed"
fi

# Launch the desktop app
echo ""
echo "Launching Ape Wellness Tracker..."
echo ""
python3 desktop_app.py "$@"

