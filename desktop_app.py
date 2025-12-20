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
import socket
import urllib.request
import urllib.parse
from pathlib import Path

# Ensure project root is on PYTHONPATH
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from backend import create_app

# Global flag to track if Flask started successfully
flask_started = threading.Event()
flask_error = None

def is_port_open(host, port, timeout=1):
    """Check if a port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def wait_for_server(url, max_wait=15, check_interval=0.5):
    """Wait for the Flask server to be ready and serving pages."""
    import urllib.error
    for attempt in range(int(max_wait / check_interval)):
        try:
            response = urllib.request.urlopen(url, timeout=2)
            status_code = response.getcode()
            # Accept 200 (OK) or 302 (redirect, like to login page)
            if status_code in (200, 302):
                print(f"Server responded with status {status_code} on attempt {attempt + 1}", file=sys.stderr)
                return True
        except urllib.error.URLError as e:
            # Connection refused or not ready yet - keep trying
            if attempt == 0:
                print(f"Waiting for server... (attempt {attempt + 1})", file=sys.stderr)
        except Exception as e:
            # Other errors - log but keep trying
            if attempt == 0:
                print(f"Server check error: {e}", file=sys.stderr)
        time.sleep(check_interval)
    print(f"Server did not respond after {max_wait} seconds", file=sys.stderr)
    return False

def log_error(message, exc=None):
    """Log errors to both console and a log file."""
    import traceback
    log_msg = f"{message}\n"
    if exc:
        log_msg += f"{traceback.format_exc()}\n"
    
    print(log_msg, file=sys.stderr)
    
    # Also write to a log file in the app bundle or current directory
    try:
        if getattr(sys, 'frozen', False):
            if sys.platform == 'darwin' and '.app/Contents/MacOS/' in sys.executable:
                log_dir = Path(sys.executable).parent.parent.parent
            else:
                log_dir = Path(sys.executable).parent
        else:
            log_dir = Path(__file__).parent
        
        log_file = log_dir / 'ape_tracker_error.log'
        with open(log_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {log_msg}\n")
    except Exception:
        pass  # Don't fail if we can't write the log

def run_flask_app():
    """Run the Flask app in a background thread for pywebview."""
    global flask_started, flask_error
    try:
        app = create_app()
        print("Flask app created successfully", file=sys.stderr)
        flask_started.set()
        app.run(host='127.0.0.1', port=5003, debug=False, use_reloader=False)
    except Exception as e:
        flask_error = str(e)
        log_error(f"Error starting Flask app: {e}", e)
        flask_started.set()  # Set even on error so we don't wait forever

def launch_with_pywebview(debug_mode: bool) -> None:
    """Launch the desktop shell using pywebview."""
    import webview

    print("Starting Flask server in background thread...", file=sys.stderr)
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # Wait for Flask server to be ready
    print("Waiting for Flask server to start...", file=sys.stderr)
    server_url = "http://127.0.0.1:5003"
    
    # Wait for Flask to start (either successfully or with error)
    flask_started.wait(timeout=15)
    
    # Check if there was an error
    if flask_error:
        error_msg = f"Failed to start Flask server:\n{flask_error}\n\nCheck ape_tracker_error.log for details."
        log_error(error_msg)
        if debug_mode:
            print(error_msg, file=sys.stderr)
        # Show error dialog
        try:
            webview.create_window(
                "Error - Ape Wellness Tracker",
                html=f"<html><body style='font-family: Arial; padding: 20px;'><h1>Error</h1><p>{error_msg}</p><p>Please check the error log file for details.</p></body></html>",
                width=600,
                height=400,
                resizable=False
            )
            webview.start(debug=debug_mode)
        except:
            pass
        return
    
    # Wait for server to actually respond with HTTP
    server_ready = wait_for_server(server_url, max_wait=20)
    
    if not server_ready:
        error_msg = "Flask server did not respond in time. The app window may appear blank."
        log_error(error_msg)
        print(f"WARNING: {error_msg}", file=sys.stderr)
        print("The window will still open, but may show a blank screen.", file=sys.stderr)
        # Continue anyway - maybe server is just slow
    else:
        print(f"Flask server is ready at {server_url}", file=sys.stderr)
    
    # Give it one more moment to ensure everything is ready
    # This extra wait helps when launched via 'open' command
    time.sleep(1.0)
    
    print(f"Opening webview window with URL: {server_url}", file=sys.stderr)

    # Enable downloads in webview (required for file downloads in desktop app)
    # Note: On macOS, downloads may not work natively
    webview.settings["ALLOW_DOWNLOADS"] = True

    # Create API class for JavaScript-Python bridge to handle downloads
    class DownloadAPI:
        def open_url(self, url):
            """Open URL in system browser (for downloads on macOS)"""
            import webbrowser
            try:
                webbrowser.open(url)
                return True
            except Exception as e:
                print(f"Error opening URL in browser: {e}", file=sys.stderr)
                return False

    download_api = DownloadAPI()

    window = webview.create_window(
        "Ape Meal Tracker",
        server_url,
        width=1400,
        height=900,
        min_size=(1024, 768),
        resizable=True,
        fullscreen=False,
        on_top=False,
        text_select=True,  # macOS option
        easy_drag=True,    # Windows option
        js_api=download_api  # Expose API to JavaScript
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

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

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
            working_dir = str(app_bundle)
        else:
            # Windows/Linux: executable is in the same directory
            working_dir = os.path.dirname(sys.executable)
        
        # Change to the working directory
        os.chdir(working_dir)
        print(f"Changed working directory to: {working_dir}")
        
        # Verify backend directory exists
        backend_path = os.path.join(working_dir, 'backend')
        if not os.path.exists(backend_path):
            # Try looking in the PyInstaller temp directory
            if hasattr(sys, '_MEIPASS'):
                meipass_backend = os.path.join(sys._MEIPASS, 'backend')
                if os.path.exists(meipass_backend):
                    print(f"Found backend in _MEIPASS: {meipass_backend}")
    else:
        # Development mode - use project root
        project_root = Path(__file__).resolve().parent
        os.chdir(str(project_root))
        print(f"Development mode - working directory: {project_root}")

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
        import traceback
        traceback.print_exc()
        print("Starting web server only. Visit http://127.0.0.1:5003")
        run_flask_app()

if __name__ == '__main__':
    main()
