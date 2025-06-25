"""Route handlers for AIPackager v3."""

from datetime import datetime
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

from .file_persistence import save_uploaded_file
from .database import create_package, get_package, get_all_packages, create_metadata
from .metadata_extractor import extract_file_metadata
from .services.script_generator import PSADTGenerator
from .models import Package
from .package_logger import get_package_logger


def register_routes(app: Flask) -> None:
    """Register all application routes.

    Args:
        app: Flask application instance
    """

    @app.route("/")
    def index() -> str:
        """Render the landing page."""
        return render_template("index.html")

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
                # The form now submits to the API, so this route is not used for POST
                return redirect(url_for("upload"))
        return render_template("upload.html")

    @app.route("/progress/<id>")
    def progress(id: str) -> Union[str, Response, tuple[str, int]]:
        """Progress tracking page."""
        package = get_package(id)
        if not package:
            return "Package not found", 404

        # If package needs script generation, start the 5-stage pipeline
        # This handles both new uploads ("uploading") and existing packages
        # that were marked "completed" but don't have generated scripts
        if package.status == "uploading" or (
            package.status == "completed" and not package.generated_script
        ):
            try:
                from .database import update_package_status
                import requests  # type: ignore
                import threading

                # Update status to processing
                update_package_status(id, "processing")

                # Start script generation in background
                def generate_script_async() -> None:
                    try:
                        base_url = request.host_url.rstrip("/")
                        requests.post(f"{base_url}/api/packages/{id}/generate")
                    except Exception:
                        # If generation fails, mark as failed
                        try:
                            update_package_status(id, "failed")
                        except Exception:
                            pass

                # Start generation in background thread
                thread = threading.Thread(target=generate_script_async)
                thread.daemon = True
                thread.start()

            except Exception:
                # If we can't start generation, mark as failed
                from .database import update_package_status

                update_package_status(id, "failed")

        # Handle AJAX requests for progress updates
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Get real progress from database
            progress_pct = (
                package.progress_pct if package.progress_pct is not None else 0
            )

            # Map status to progress if not set
            if progress_pct == 0:
                if package.status == "uploading":
                    progress_pct = 10
                elif package.status == "processing":
                    progress_pct = 45  # Show 45% during processing
                elif package.status == "completed":
                    progress_pct = 100
                elif package.status == "failed":
                    progress_pct = 0

            return jsonify(
                {
                    "job_id": str(package.id),
                    "filename": package.filename,
                    "status": package.status,
                    "progress": progress_pct,
                    "current_step": package.current_step or "Processing",
                }
            )

        # Redirect to detail page when completed
        if package.status == "completed":
            return redirect(url_for("detail", id=id))

        # Show error message if failed
        if package.status == "failed":
            return render_template(
                "progress.html",
                job_id=id,
                error="Script generation failed. Please try again.",
            )

        return render_template("progress.html", job_id=id)

    @app.route("/detail/<id>")
    def detail(id: str) -> Union[str, tuple[str, int]]:
        """Result details page."""
        package = get_package(id)
        if not package:
            return "Package not found", 404

        # Convert 5-stage pipeline results to rendered script
        rendered_script = "No script generated yet."

        if package.generated_script:
            # Convert PSADTScript JSON back to readable PowerShell
            script_data = package.generated_script
            script_sections = []

            if script_data.get("pre_installation_tasks"):
                script_sections.append("# Pre-Installation Tasks")
                script_sections.extend(script_data["pre_installation_tasks"])
                script_sections.append("")

            if script_data.get("installation_tasks"):
                script_sections.append("# Installation Tasks")
                script_sections.extend(script_data["installation_tasks"])
                script_sections.append("")

            if script_data.get("post_installation_tasks"):
                script_sections.append("# Post-Installation Tasks")
                script_sections.extend(script_data["post_installation_tasks"])
                script_sections.append("")

            if script_data.get("uninstallation_tasks"):
                script_sections.append("# Uninstallation Tasks")
                script_sections.extend(script_data["uninstallation_tasks"])
                script_sections.append("")

            if script_data.get("post_uninstallation_tasks"):
                script_sections.append("# Post-Uninstallation Tasks")
                script_sections.extend(script_data["post_uninstallation_tasks"])
                script_sections.append("")

            # Add pipeline metadata at the end
            if package.hallucination_report or package.corrections_applied:
                script_sections.append("# 5-Stage Pipeline Results")
                if package.hallucination_report:
                    has_issues = package.hallucination_report.get(
                        "has_hallucinations", False
                    )
                    script_sections.append(
                        f"# Hallucination Detection: {'Issues Found' if has_issues else 'Clean'}"
                    )
                if package.corrections_applied:
                    script_sections.append(
                        f"# Corrections Applied: {len(package.corrections_applied)}"
                    )
                    for correction in package.corrections_applied:
                        script_sections.append(f"#   - {correction}")

            rendered_script = "\n".join(script_sections)

        return render_template(
            "detail.html",
            package=package,
            metadata=package.package_metadata,
            rendered_script=rendered_script,
        )

    @app.route("/history")
    def history() -> str:
        """Upload history page."""
        packages = get_all_packages()
        return render_template("history.html", packages=packages)

    @app.route("/api/packages", methods=["POST"])
    def api_create_package() -> Union[Response, tuple[str, int]]:
        """API endpoint to create a new package with file upload."""
        package_logger = None
        try:
            # Validate file upload
            if "installer" not in request.files:
                return jsonify({"error": "No file part"}), 400

            file = request.files["installer"]
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400

            if not file.filename.lower().endswith((".msi", ".exe")):
                return jsonify({"error": "Invalid file type"}), 400

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

            # Initialize logger for this package
            package_logger = get_package_logger(str(package.id))
            package_logger.log_step(
                "UPLOAD",
                f"Package upload started: {file.filename}",
                data={
                    "filename": file.filename,
                    "file_size": file.content_length,
                    "custom_instructions": custom_instructions,
                    "file_path": str(file_path),
                },
            )

            # Extract and store metadata
            package_logger.log_step(
                "METADATA_EXTRACTION", "Starting metadata extraction"
            )
            try:
                metadata_dict = extract_file_metadata(file_path)
                package_logger.log_step(
                    "METADATA_EXTRACTION",
                    "Metadata extraction completed successfully",
                    data={"metadata_keys": list(metadata_dict.keys())},
                )
            except Exception as e:
                package_logger.log_error(
                    "METADATA_EXTRACTION",
                    e,
                    {
                        "file_path": str(file_path),
                        "file_type": file.filename.split(".")[-1].lower(),
                    },
                )
                # Continue with empty metadata dict
                metadata_dict = {}
                package_logger.log_step(
                    "METADATA_EXTRACTION",
                    "Continuing with empty metadata due to extraction failure",
                )

            # Get PSADT variables with fallback mapping
            package_logger.log_step("PSADT_MAPPING", "Starting PSADT variable mapping")
            try:
                from .metadata_extractor import MetadataExtractor

                extractor = MetadataExtractor()
                psadt_vars = extractor.get_psadt_variables(metadata_dict)
                package_logger.log_step(
                    "PSADT_MAPPING",
                    "PSADT mapping completed",
                    data={"psadt_vars": psadt_vars},
                )
            except Exception as e:
                package_logger.log_error("PSADT_MAPPING", e)
                psadt_vars = {}

            # Store metadata in database
            package_logger.log_step("DATABASE_STORAGE", "Storing metadata in database")
            try:
                create_metadata(
                    package_id=package.id,
                    product_name=psadt_vars.get("appName")
                    or metadata_dict.get("product_name"),
                    version=psadt_vars.get("appVersion")
                    or metadata_dict.get("version"),
                    publisher=psadt_vars.get("appVendor")
                    or metadata_dict.get("publisher"),
                    install_date=metadata_dict.get("install_date"),
                    uninstall_string=metadata_dict.get("uninstall_string"),
                    estimated_size=metadata_dict.get("estimated_size"),
                    product_code=psadt_vars.get("productCode")
                    or metadata_dict.get("product_code"),
                    upgrade_code=metadata_dict.get("upgrade_code"),
                    language=metadata_dict.get("language"),
                    architecture=metadata_dict.get("architecture"),
                )
                package_logger.log_step(
                    "DATABASE_STORAGE", "Metadata stored successfully"
                )
            except Exception as e:
                package_logger.log_error("DATABASE_STORAGE", e)

            package_logger.log_step(
                "UPLOAD_COMPLETE",
                f"Package upload completed successfully: {package.id}",
            )

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
            if package_logger:
                package_logger.log_error("UPLOAD_FAILED", e)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/packages/<package_id>/generate", methods=["POST"])
    def api_generate_script(package_id: str) -> Union[Response, tuple[str, int]]:
        """API endpoint to generate a PSADT script using the 5-stage pipeline."""
        package_logger = get_package_logger(package_id)
        try:
            package = get_package(package_id)
            if not package:
                return jsonify({"error": "Package not found"}), 404

            package_logger.log_step("SCRIPT_GENERATION", "Starting 5-stage pipeline")

            # Update package status to processing
            from .database import update_package_status

            update_package_status(package_id, "processing")
            package_logger.log_step(
                "STATUS_UPDATE", "Package status updated to processing"
            )

            # Generate script using 5-stage pipeline
            package_logger.log_5_stage_pipeline(1, "Instruction Processing", "Starting")
            generator = PSADTGenerator()

            try:
                psadt_script = generator.generate_script(
                    package.custom_instructions or "Install the application"
                )
                package_logger.log_step(
                    "PIPELINE_COMPLETE",
                    "5-stage pipeline completed successfully",
                    data={
                        "has_hallucinations": psadt_script.hallucination_report.get(
                            "has_hallucinations", False
                        )
                        if psadt_script.hallucination_report
                        else False,
                        "corrections_count": len(
                            psadt_script.corrections_applied or []
                        ),
                    },
                )
            except Exception as e:
                package_logger.log_error("PIPELINE_FAILED", e)
                update_package_status(package_id, "failed")
                return jsonify({"error": f"Pipeline failed: {str(e)}"}), 500

            # Update the package with pipeline results
            package_logger.log_step(
                "DATABASE_UPDATE", "Storing pipeline results in database"
            )
            from .database import get_database_service

            db_service = get_database_service()
            session = db_service.get_session()

            try:
                # Get fresh package instance from this session
                from uuid import UUID

                uuid_obj = UUID(package_id)
                db_package = (
                    session.query(Package).filter(Package.id == uuid_obj).first()
                )

                if db_package:
                    # Store pipeline results in database
                    db_package.generated_script = psadt_script.model_dump()
                    db_package.hallucination_report = psadt_script.hallucination_report
                    db_package.corrections_applied = psadt_script.corrections_applied
                    db_package.pipeline_metadata = {
                        "generation_timestamp": datetime.now().isoformat(),
                        "model_used": "gpt-4o-mini",
                        "pipeline_version": "5-stage-v1",
                    }
                    db_package.status = "completed"

                    session.commit()
                    package_logger.log_step(
                        "DATABASE_UPDATE", "Pipeline results stored successfully"
                    )

                    # Also save as JSON file for backup/debugging
                    instance_dir = Path(current_app.instance_path)
                    script_path = instance_dir / f"{package_id}.json"
                    with open(script_path, "w") as f:
                        f.write(psadt_script.model_dump_json(indent=4))

                    package_logger.log_step(
                        "FILE_BACKUP", f"Script backup saved to {script_path}"
                    )

                    package_logger.log_step(
                        "GENERATION_COMPLETE",
                        f"Script generation completed successfully for package {package_id}",
                    )

                    return jsonify(
                        {
                            "package_id": str(package.id),
                            "message": "Script generation completed successfully.",
                            "status": "completed",
                            "has_hallucinations": psadt_script.hallucination_report.get(
                                "has_hallucinations", False
                            )
                            if psadt_script.hallucination_report
                            else False,
                            "corrections_applied": len(
                                psadt_script.corrections_applied or []
                            ),
                            "script_path": str(script_path),
                            "log_file": str(package_logger.get_log_file_path()),
                        }
                    )
                else:
                    package_logger.log_error(
                        "DATABASE_UPDATE", Exception("Package not found in database")
                    )
                    return jsonify({"error": "Package not found in database"}), 404

            finally:
                session.close()

        except Exception as e:
            # Update package status to failed
            package_logger.log_error("GENERATION_FAILED", e)
            try:
                update_package_status(package_id, "failed")
            except Exception:
                pass
            return jsonify({"error": str(e)}), 500

    @app.route("/api/render/<package_id>", methods=["POST"])
    def api_render_package(package_id: str) -> Union[Response, tuple[str, int]]:
        """API endpoint for manual re-rendering of PSADT scripts."""
        try:
            package = get_package(package_id)
            if not package:
                return jsonify({"error": "Package not found"}), 404

            # Import ScriptRenderer
            from .script_renderer import ScriptRenderer

            # Get AI sections from request body (for testing/manual rendering)
            request_data = request.get_json() or {}
            ai_sections = request_data.get(
                "ai_sections",
                {
                    "pre_installation_tasks": "# Manual render - no AI sections provided",
                    "installation_tasks": "# Manual render - no AI sections provided",
                    "post_installation_tasks": "# Manual render - no AI sections provided",
                    "uninstallation_tasks": "# Manual render - no AI sections provided",
                    "post_uninstallation_tasks": "# Manual render - no AI sections provided",
                },
            )

            # Initialize renderer and render script
            renderer = ScriptRenderer()
            rendered_script = renderer.render_psadt_script(package, ai_sections)

            # Build response
            response_data = {
                "package_id": str(package.id),
                "filename": package.filename,
                "rendered_script": rendered_script,
                "render_timestamp": datetime.now().isoformat(),
                "ai_sections_provided": list(ai_sections.keys()),
            }

            # Include metadata if available
            if package.package_metadata:
                metadata = package.package_metadata
                response_data["metadata"] = {
                    "product_name": metadata.product_name,
                    "version": metadata.version,
                    "publisher": metadata.publisher,
                    "architecture": metadata.architecture,
                    "product_code": metadata.product_code,
                }

            return jsonify(response_data)

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

    @app.route("/logs/<package_id>")
    def view_logs(package_id: str) -> Union[str, tuple[str, int]]:
        """View logs for a specific package."""
        package = get_package(package_id)
        if not package:
            return "Package not found", 404

        package_logger = get_package_logger(package_id)
        logs = package_logger.get_logs()
        log_file_path = package_logger.get_log_file_path()

        return render_template(
            "logs.html",
            package=package,
            logs=logs,
            log_file_path=log_file_path,
        )

    @app.route("/api/packages/<package_id>/logs", methods=["GET"])
    def api_get_logs(package_id: str) -> Union[Response, tuple[str, int]]:
        """API endpoint to get logs for a specific package."""
        try:
            package = get_package(package_id)
            if not package:
                return jsonify({"error": "Package not found"}), 404

            package_logger = get_package_logger(package_id)
            logs = package_logger.get_logs()
            log_file_path = package_logger.get_log_file_path()

            return jsonify(
                {
                    "package_id": package_id,
                    "filename": package.filename,
                    "logs": logs,
                    "log_file_path": str(log_file_path) if log_file_path else None,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500
