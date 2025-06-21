"""Route handlers for AIPackager v3."""

from flask import Flask, jsonify, redirect, render_template, request, url_for

from .progress import get_job, start_job


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        """File upload page."""
        if request.method == "POST":
            if "installer" not in request.files:
                return "No file part", 400
            file = request.files["installer"]
            if file.filename == "":
                return "No selected file", 400
            if file:
                job_id = start_job(file.filename)
                return redirect(url_for("progress", id=job_id))
        return render_template("upload.html")

    @app.route("/progress/<id>")
    def progress(id: str):
        """Progress tracking page."""
        job = get_job(id)
        if not job:
            return "Job not found", 404

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(job)

        return render_template("progress.html", job_id=id)

    @app.route("/detail/<id>")
    def detail(id: str):
        """Result details page."""
        return render_template("detail.html", job_id=id)

    @app.route("/history")
    def history():
        """Upload history page."""
        return render_template("history.html")
