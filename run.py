# Entry point to start Flask app

"""
Application entry point for the Ape Wellness Tracker.

This script creates and runs the Flask app using the factory pattern
defined in backend/__init__.py.
"""

from backend import create_app

app = create_app()

if __name__ == '__main__':
    import sys
    port = 5000
    if '--port' in sys.argv:
        try:
            port_index = sys.argv.index('--port')
            port = int(sys.argv[port_index + 1])
        except (ValueError, IndexError):
            print("Invalid port number. Using default port 5000.")
    
    app.run(debug=True, port=port)
