"""Flask application factory for AIPackager v3."""

from typing import Optional, Tuple
from flask import Flask
from flask_socketio import SocketIO
from .extensions import socketio
from .routes import register_routes


def create_app(config: Optional[dict] = None) -> Tuple[Flask, SocketIO]:
    """Create and configure Flask application instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Tuple[Flask, SocketIO]: Configured Flask application and SocketIO instances
    """
    app = Flask(__name__)

    # Apply configuration if provided
    if config:
        app.config.update(config)

    # Initialize extensions
    socketio.init_app(app)

    # Register routes
    register_routes(app)

    # Resume pending jobs on startup
    with app.app_context():
        try:
            from src.aipackager.workflow import PackageRequest

            PackageRequest.resume_pending_jobs()
        except Exception as e:
            app.logger.error(f"Failed to resume pending jobs on startup: {e}")

    return app, socketio
