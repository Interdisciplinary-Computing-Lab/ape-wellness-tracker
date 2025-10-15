#!/usr/bin/env python3
"""
Desktop Application for Ape Wellness Tracker using FlaskWebGUI

This script creates a desktop application wrapper around the Flask web application
using FlaskWebGUI. It's much simpler than pywebview and specifically designed
for Flask applications.

Usage:
    python desktop_app.py

Features:
    - Native desktop window
    - Automatic Flask server startup
    - Cross-platform compatibility
    - Simple and lightweight
    - Built specifically for Flask apps
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from flaskwebgui import FlaskUI
    from backend import create_app
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Main entry point for the desktop application"""
    print("Starting Ape Wellness Tracker Desktop App...")
    
    # Check if we're running from a packaged executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = os.path.dirname(sys.executable)
        os.chdir(application_path)
    
    # Create Flask app
    app = create_app()
    
    # Create FlaskWebGUI instance
    ui = FlaskUI(
        app=app,
        server="flask",
        width=1200,
        height=800,
        fullscreen=False,
        browser_path=None  # Use default browser
    )
    
    # Run the desktop application
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()