"""Flask application factory for AIPackager v3."""

from typing import Optional
from flask import Flask

from .routes import register_routes


def create_app(config: Optional[dict] = None) -> Flask:
    """Create and configure Flask application instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Apply configuration if provided
    if config:
        app.config.update(config)

    # Register routes
    register_routes(app)

    # Resume pending jobs on startup
    with app.app_context():
        try:
            from src.aipackager.workflow import PackageRequest

            PackageRequest.resume_pending_jobs()
        except Exception as e:
            app.logger.error(f"Failed to resume pending jobs on startup: {e}")

    return app
