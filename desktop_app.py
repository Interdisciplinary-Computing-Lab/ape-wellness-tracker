#!/usr/bin/env python3
"""
Desktop application entry point for Ape Wellness Tracker.

Tries to launch the Flask app inside a native window using pywebview first,
then falls back to FlaskWebGUI if pywebview is unavailable.

Usage:
    python desktop_app.py           # Normal mode
    python desktop_app.py --debug   # Enable developer console (pywebview only)
    python desktop_app.py -d
"""

import os
import sys
import time
import threading
from pathlib import Path

# Ensure project root is on PYTHONPATH
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from backend import create_app

def run_flask_app():
    """Run the Flask app in a background thread for pywebview."""
    app = create_app()
    app.run(host='127.0.0.1', port=5003, debug=True, use_reloader=False)

def launch_with_pywebview(debug_mode: bool) -> None:
    """Launch the desktop shell using pywebview."""
    import webview

    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # Allow Flask a moment to start
    time.sleep(1.5)

    window = webview.create_window(
        "Ape Wellness Tracker",
        "http://127.0.0.1:5003",
        width=1400,
        height=900,
        min_size=(1024, 768),
        resizable=True,
        fullscreen=False,
        on_top=False,
        text_select=True,  # macOS option
        easy_drag=True,    # Windows option
    )

    webview.start(debug=debug_mode)

def launch_with_flaskwebgui() -> None:
    """Fallback desktop shell using FlaskWebGUI."""
    from flaskwebgui import FlaskUI

    app = create_app()
    ui = FlaskUI(
        app=app,
        server="flask",
        width=1200,
        height=800,
        fullscreen=False,
    )
    ui.run()

def main():
    """Main entry point for the desktop application."""
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv

    # Align working directory when packaged
    if getattr(sys, 'frozen', False):
        # For macOS .app bundles, sys.executable is inside Contents/MacOS/
        # We need to go up to the app bundle root
        if sys.platform == 'darwin' and '.app/Contents/MacOS/' in sys.executable:
            # macOS app bundle: go up from Contents/MacOS/executable to .app root
            app_bundle = Path(sys.executable).parent.parent.parent
            os.chdir(str(app_bundle))
        else:
            # Windows/Linux: executable is in the same directory
            os.chdir(os.path.dirname(sys.executable))

    try:
        launch_with_pywebview(debug_mode)
    except ImportError:
        print("pywebview not available, falling back to FlaskWebGUI...")
        try:
            launch_with_flaskwebgui()
        except ImportError as exc:
            print(f"Unable to start desktop shell: {exc}")
            print("Install requirements with: pip install -r requirements.txt")
            print("You can still run the web app via: python run.py")
            sys.exit(1)
    except Exception as exc:
        print(f"Desktop launcher error: {exc}")
        print("Starting web server only. Visit http://127.0.0.1:5003")
        run_flask_app()

if __name__ == '__main__':
    main()
