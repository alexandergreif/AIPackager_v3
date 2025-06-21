"""Route handlers for AIPackager v3."""

from flask import Flask, render_template


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/upload")
    def upload():
        """File upload page."""
        return render_template("upload.html")

    @app.route("/progress/<id>")
    def progress(id: str):
        """Progress tracking page."""
        return render_template("progress.html", job_id=id)

    @app.route("/detail/<id>")
    def detail(id: str):
        """Result details page."""
        return render_template("detail.html", job_id=id)

    @app.route("/history")
    def history():
        """Upload history page."""
        return render_template("history.html")
