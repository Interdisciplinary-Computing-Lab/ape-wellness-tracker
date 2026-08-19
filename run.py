# Entry point to start Flask app

"""
Application entry point for the Ape Wellness Tracker.

This script creates and runs the Flask app using the factory pattern
defined in backend/__init__.py.
"""

from backend import create_app

app = create_app()

if __name__ == '__main__':
    import os
    import sys
    port = 5003
    if '--port' in sys.argv:
        try:
            port_index = sys.argv.index('--port')
            port = int(sys.argv[port_index + 1])
        except (ValueError, IndexError):
            print("Invalid port number. Using default port 5003.")

    debug = os.getenv('FLASK_DEBUG', '0').strip().lower() in ('1', 'true', 'yes', 'on')
    app.run(debug=debug, port=port)
