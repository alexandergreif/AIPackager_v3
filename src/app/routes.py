"""Route handlers for AIPackager v3."""

from pathlib import Path
from typing import Union
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    Response,
    current_app,
)

import json
from .file_persistence import save_uploaded_file
from .database import create_package, get_package, get_all_packages, create_metadata
from .progress import get_job, start_job
from .metadata_extractor import extract_file_metadata


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/")
    def index() -> Response:
        """Redirect to the upload page."""
        return redirect(url_for("upload"))

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

        if job["status"] == "Uploading":
            # Simulate processing
            from .progress import set_job_progress
            import time

            set_job_progress(id, 25, "Extracting metadata...")
            time.sleep(1)
            set_job_progress(id, 50, "Generating script...")
            time.sleep(1)
            set_job_progress(id, 75, "Finalizing script...")
            time.sleep(1)
            set_job_progress(id, 100, "Completed")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(job)

        if job["status"] == "Completed":
            return redirect(url_for("detail", id=id))

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

    @app.route("/api/packages", methods=["POST"])
    def api_create_package() -> Union[Response, tuple[str, int]]:
        """API endpoint to create a new package with file upload."""
        try:
            # Validate file upload
            if "installer" not in request.files:
                return jsonify({"error": "No file part"}), 400

            file = request.files["installer"]
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400

            # Get custom instructions
            custom_instructions = request.form.get("custom_instructions", "")

            # Get instance directory
            instance_dir = Path(current_app.instance_path)

            # Save file with UUID naming
            file_id, file_path = save_uploaded_file(file, instance_dir)

            # Create package record in database
            package = create_package(
                filename=file.filename,
                file_path=file_path,
                custom_instructions=custom_instructions,
            )

            # Extract and store metadata
            metadata_dict = extract_file_metadata(file_path)
            create_metadata(package_id=package.id, metadata=json.dumps(metadata_dict))

            # Return package information
            return jsonify(
                {
                    "package_id": str(package.id),
                    "filename": package.filename,
                    "status": package.status,
                    "upload_time": package.upload_time.isoformat(),
                    "custom_instructions": package.custom_instructions,
                }
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/packages", methods=["GET"])
    def api_list_packages() -> Response:
        """API endpoint to list all packages."""
        try:
            packages = get_all_packages()

            package_list = []
            for package in packages:
                package_data = {
                    "package_id": str(package.id),
                    "filename": package.filename,
                    "status": package.status,
                    "upload_time": package.upload_time.isoformat(),
                    "custom_instructions": package.custom_instructions,
                }

                # Include metadata if available
                if package.package_metadata:
                    metadata = package.package_metadata
                    package_data["metadata"] = {
                        "product_name": metadata.product_name,
                        "version": metadata.version,
                        "publisher": metadata.publisher,
                        "install_date": metadata.install_date,
                        "uninstall_string": metadata.uninstall_string,
                        "estimated_size": metadata.estimated_size,
                        "product_code": metadata.product_code,
                        "upgrade_code": metadata.upgrade_code,
                        "language": metadata.language,
                        "architecture": metadata.architecture,
                    }

                package_list.append(package_data)

            return jsonify({"packages": package_list})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/packages/<package_id>", methods=["GET"])
    def api_get_package(package_id: str) -> Union[Response, tuple[str, int]]:
        """API endpoint to get a specific package."""
        try:
            package = get_package(package_id)
            if not package:
                return jsonify({"error": "Package not found"}), 404

            package_data = {
                "package_id": str(package.id),
                "filename": package.filename,
                "status": package.status,
                "upload_time": package.upload_time.isoformat(),
                "custom_instructions": package.custom_instructions,
            }

            # Include metadata if available
            if package.package_metadata:
                metadata = package.package_metadata
                package_data["metadata"] = {
                    "product_name": metadata.product_name,
                    "version": metadata.version,
                    "publisher": metadata.publisher,
                    "install_date": metadata.install_date,
                    "uninstall_string": metadata.uninstall_string,
                    "estimated_size": metadata.estimated_size,
                    "product_code": metadata.product_code,
                    "upgrade_code": metadata.upgrade_code,
                    "language": metadata.language,
                    "architecture": metadata.architecture,
                }

            return jsonify(package_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500
