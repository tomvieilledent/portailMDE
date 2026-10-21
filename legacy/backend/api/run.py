"""Small runner for local development.

Runs the Flask application created by `create_app()` when executed as a
script. This file is intended for local development only.
"""

# eventlet monkey-patching MUST run before any other import (stdlib socket,
# threading, ...) so Flask-SocketIO can serve real WebSocket connections.
import eventlet
eventlet.monkey_patch()

from backend.api.app import create_app  # noqa: E402
from backend.api.sockets import socketio  # noqa: E402

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
