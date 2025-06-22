"""Route handlers for AIPackager v3."""

from typing import Union
from flask import Flask, jsonify, redirect, render_template, request, url_for, Response

from .progress import get_job, start_job


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/upload", methods=["GET", "POST"])
    def upload() -> Union[str, Response, tuple[str, int]]:
        """File upload page."""
        if request.method == "POST":
            if "installer" not in request.files:
                return "No file part", 400
            file = request.files["installer"]
            if file.filename == "":
                return "No selected file", 400
            if file:
                custom_instructions = request.form.get("custom_instructions", "")
                job_id = start_job(file.filename, custom_instructions)
                return redirect(url_for("progress", id=job_id))
        return render_template("upload.html")

    @app.route("/progress/<id>")
    def progress(id: str) -> Union[str, Response, tuple[str, int]]:
        """Progress tracking page."""
        job = get_job(id)
        if not job:
            return "Job not found", 404

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(job)

        return render_template("progress.html", job_id=id)

    @app.route("/detail/<id>")
    def detail(id: str) -> Union[str, tuple[str, int]]:
        """Result details page."""
        job = get_job(id)
        if not job:
            return "Job not found", 404
        return render_template("detail.html", job_id=id)

    @app.route("/history")
    def history() -> str:
        """Upload history page."""
        return render_template("history.html")
