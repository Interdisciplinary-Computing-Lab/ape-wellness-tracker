#!/usr/bin/env python3
"""
Desktop application entry point for Ape Wellness Tracker.

This script launches the Flask app in a desktop window using pywebview.
Works on both Windows and macOS.

Usage:
    python desktop_app.py          # Normal mode (no developer tools)
    python desktop_app.py --debug # Debug mode (shows developer console)
    python desktop_app.py -d      # Short form for debug mode
"""

import threading
import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app

def run_flask_app():
    """Run Flask app in a separate thread."""
    app = create_app()
    # Use the exact same configuration as run.py
    # This ensures desktop app behaves identically to web app
    app.run(host='127.0.0.1', port=5003, debug=True, use_reloader=False)

def main():
    """Main entry point for desktop application."""
    try:
        import webview
        
        # Check if debug mode is requested via command line argument
        debug_mode = '--debug' in sys.argv or '-d' in sys.argv
        
        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        
        # Wait a moment for Flask to start
        time.sleep(1.5)
        
        # Get the window title
        app_name = "Ape Wellness Tracker"
        
        # Create the webview window
        # Use a larger default size for better UX
        # Note: webview should handle redirects automatically, just like a browser
        window = webview.create_window(
            app_name,
            'http://127.0.0.1:5003',
            width=1400,
            height=900,
            min_size=(1024, 768),
            resizable=True,
            fullscreen=False,
            on_top=False,
            # macOS specific options
            text_select=True,
            # Windows specific options  
            easy_drag=True,
        )
        
        
        # Start the webview event loop
        # Debug mode shows developer console (useful for troubleshooting)
        # Use --debug or -d flag to enable: python desktop_app.py --debug
        webview.start(debug=debug_mode)
        
    except ImportError:
        print("Error: pywebview is not installed.")
        print("Please install it with: pip install pywebview")
        print("\nAlternatively, you can run the web app directly:")
        print("  python run.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting desktop application: {e}")
        print("\nFalling back to web server mode...")
        print("You can access the app at http://127.0.0.1:5003")
        run_flask_app()

if __name__ == '__main__':
    main()

