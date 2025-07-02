"""Route handlers for AIPackager v3."""

from datetime import datetime
from pathlib import Path
from typing import Union, Any, cast, Generator
from uuid import UUID
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
from .script_renderer import ScriptRenderer
from .services.metrics_service import MetricsService
from .models import Package
from .package_logger import get_package_logger
from .crawl_logger import get_crawl_logger
from .extensions import socketio
import queue
import json
import concurrent.futures
import anyio

progress_queues: dict[str, queue.Queue[Any]] = {}


def run_mcp_in_thread(async_func: Any, *args: Any, **kwargs: Any) -> Any:
    """Run async MCP function in a separate thread to avoid asyncio conflicts."""

    async def async_wrapper() -> Any:
        return await async_func(*args, **kwargs)

    def run_async() -> Any:
        return anyio.run(async_wrapper)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_async)
        return future.result(timeout=30)


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
                return cast(Response, redirect(url_for("upload")))

        return render_template("upload.html")

    @app.route("/progress/<id>")
    def progress(id: str) -> Union[str, Response, tuple[str, int]]:
        """Progress tracking page."""
        package = get_package(id)
        if not package:
            return "Package not found", 404

        # If package needs script generation, start the 5-stage pipeline
        if package.status == "uploading" or (
            package.status == "completed" and not package.generated_script
        ):
            try:
                from .database import update_package_status, get_database_service
                import threading

                # Update status to processing
                update_package_status(id, "processing")

                # Start script generation in background without HTTP self-call
                def generate_script_async() -> None:
                    from uuid import UUID

                    try:
                        with app.app_context():
                            db_service = get_database_service()
                            session = db_service.get_session()
                            try:
                                package_obj = session.get(Package, UUID(id))
                                if not package_obj:
                                    update_package_status(id, "failed")
                                    return

                                package_logger = get_package_logger(str(package_obj.id))
                                generator = PSADTGenerator()

                                try:
                                    psadt_script = generator.generate_script(
                                        package_obj.custom_instructions
                                        or "Install the application",
                                        package=package_obj,
                                        session=session,
                                        progress_queue=progress_queues.get(id),
                                    )
                                except Exception as e:
                                    package_logger.log_error("PIPELINE_FAILED", e)
                                    package_obj.status = "failed"
                                    session.commit()
                                    if id in progress_queues:
                                        progress_queues[id].put(
                                            {
                                                "status": "failed",
                                                "error": str(e),
                                            }
                                        )
                                        progress_queues[id].put(None)
                                    return

                                package_obj.generated_script = psadt_script.model_dump()
                                package_obj.hallucination_report = (
                                    psadt_script.hallucination_report
                                )
                                package_obj.corrections_applied = (
                                    psadt_script.corrections_applied
                                )
                                package_obj.pipeline_metadata = {
                                    "generation_timestamp": datetime.now().isoformat(),
                                    "model_used": "gpt-4.1-mini",
                                    "pipeline_version": "5-stage-v1",
                                }
                                package_obj.status = "completed"
                                session.commit()

                                if id in progress_queues:
                                    progress_queues[id].put(
                                        {
                                            "status": "completed",
                                            "progress": 100,
                                            "current_step": "Completed",
                                        }
                                    )
                                    progress_queues[id].put(None)

                                instance_dir = Path(current_app.instance_path)
                                script_path = instance_dir / f"{package_obj.id}.json"
                                with open(script_path, "w") as f:
                                    f.write(psadt_script.model_dump_json(indent=4))

                                package_logger.log_step(
                                    "GENERATION_COMPLETE",
                                    f"Script generation completed successfully for package {package_obj.id}",
                                )
                            finally:
                                session.close()
                    except Exception:
                        try:
                            with app.app_context():
                                update_package_status(id, "failed")
                        except Exception:
                            pass

                # Start generation in background thread
                thread = threading.Thread(target=generate_script_async)
                thread.daemon = True
                thread.start()

            except Exception:
                from .database import update_package_status

                update_package_status(id, "failed")

        return render_template("progress.html", job_id=id)

    @app.route("/stream-progress/<id>")
    def stream_progress(id: str) -> Response:
        def generate() -> Generator[str, None, None]:
            progress_queues[id] = queue.Queue()
            while True:
                try:
                    data = progress_queues[id].get(timeout=30)
                    if data is None:
                        break
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    # Send a keep-alive comment
                    yield ":\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/detail/<id>")
    def detail(id: str) -> Union[str, tuple[str, int]]:
        """Result details page."""
        package = get_package(id)
        if not package:
            return "Package not found", 404

        # Convert 5-stage pipeline results to rendered script
        rendered_script = "No script generated yet."
        if package.generated_script:
            renderer = ScriptRenderer()
            rendered_script = renderer.render_psadt_script(
                package=package, ai_sections=package.generated_script
            )

        # Calculate display metrics
        metrics_service = MetricsService(package.__dict__)
        display_metrics = metrics_service.get_display_metrics()

        # Parse RAG documentation if available
        rag_documentation = None
        if package.rag_documentation:
            try:
                import json

                rag_documentation = json.loads(package.rag_documentation)
            except (json.JSONDecodeError, TypeError):
                rag_documentation = package.rag_documentation

        return render_template(
            "detail.html",
            package=package,
            metadata=package.package_metadata,
            rendered_script=rendered_script,
            display_metrics=display_metrics,
            rag_documentation=rag_documentation,
        )

    @app.route("/history")
    def history() -> str:
        """Upload history page."""
        packages = get_all_packages()
        return render_template("history.html", packages=packages)

    @app.route("/tools")
    def tools() -> str:
        """Render the maintenance and tools page."""
        return render_template("tools.html")

    @app.route("/api/packages", methods=["POST"])
    def api_create_package() -> Response | tuple[Response, int]:
        """API endpoint to create a new package with file upload."""
        package_logger = None

        try:
            # Validate file upload
            if "installer" not in request.files:
                return jsonify({"error": "No file part"}), 400

            file = request.files["installer"]
            filename = file.filename or ""
            if filename == "":
                return jsonify({"error": "No selected file"}), 400

            if not filename.lower().endswith((".msi", ".exe")):
                return jsonify({"error": "Invalid file type"}), 400

            # Get custom instructions
            custom_instructions = request.form.get("custom_instructions", "")

            # Get instance directory
            instance_dir = Path(current_app.instance_path)

            # Save file with UUID naming
            file_id, file_path = save_uploaded_file(file, instance_dir)

            # Create package record in database
            package = create_package(
                filename=filename,
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
                        "file_type": (
                            filename.split(".")[-1].lower() if filename else ""
                        ),
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
                executable_names = extractor.extract_executable_names(file_path)
                package_logger.log_step(
                    "PSADT_MAPPING",
                    "PSADT mapping completed",
                    data={
                        "psadt_vars": psadt_vars,
                        "executable_names": executable_names,
                    },
                )
            except Exception as e:
                package_logger.log_error("PSADT_MAPPING", e)
                psadt_vars = {}
                executable_names = []

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
                    executable_names=executable_names,
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

    @app.route("/api/packages/<uuid:package_id>/generate", methods=["POST"])
    def api_generate_script(package_id: UUID) -> Response | tuple[Response, int]:
        """API endpoint to generate a PSADT script using the 5-stage pipeline."""
        package_logger = get_package_logger(str(package_id))
        from .database import get_database_service

        db_service = get_database_service()
        session = db_service.get_session()
        try:
            package = session.get(Package, package_id)
            if not package:
                session.close()
                return jsonify({"error": "Package not found"}), 404

            package_logger.log_step("SCRIPT_GENERATION", "Starting 5-stage pipeline")

            package.status = "processing"
            session.commit()
            package_logger.log_step(
                "STATUS_UPDATE", "Package status updated to processing"
            )

            # Generate script using 5-stage pipeline
            package_logger.log_5_stage_pipeline(1, "Instruction Processing", "Starting")
            generator = PSADTGenerator()

            try:
                psadt_script = generator.generate_script(
                    package.custom_instructions or "Install the application",
                    package=package,
                    session=session,
                )
                package_logger.log_step(
                    "PIPELINE_COMPLETE",
                    "5-stage pipeline completed successfully",
                    data={
                        "has_hallucinations": (
                            psadt_script.hallucination_report.get(
                                "has_hallucinations", False
                            )
                            if psadt_script.hallucination_report
                            else False
                        ),
                        "corrections_count": len(
                            psadt_script.corrections_applied or []
                        ),
                    },
                )
            except Exception as e:
                package_logger.log_error("PIPELINE_FAILED", e)
                package.status = "failed"
                session.commit()
                return jsonify({"error": f"Pipeline failed: {str(e)}"}), 500

            # Update the package with pipeline results
            package_logger.log_step(
                "DATABASE_UPDATE", "Storing pipeline results in database"
            )

            try:
                db_package = package

                if db_package:
                    # Store pipeline results in database
                    db_package.generated_script = psadt_script.model_dump()
                    db_package.hallucination_report = psadt_script.hallucination_report
                    db_package.corrections_applied = psadt_script.corrections_applied
                    db_package.pipeline_metadata = {
                        "generation_timestamp": datetime.now().isoformat(),
                        "model_used": "gpt-4.1-mini",
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

                    return (
                        jsonify(
                            {
                                "package_id": str(package.id),
                                "message": "Script generation completed successfully.",
                                "status": "completed",
                                "has_hallucinations": (
                                    psadt_script.hallucination_report.get(
                                        "has_hallucinations", False
                                    )
                                    if psadt_script.hallucination_report
                                    else False
                                ),
                                "corrections_applied": len(
                                    psadt_script.corrections_applied or []
                                ),
                                "script_path": str(script_path),
                                "log_file": str(package_logger.get_log_file_path()),
                            }
                        ),
                        202,
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
                if package:
                    package.status = "failed"
                    session.commit()
            except Exception:
                pass
            return jsonify({"error": str(e)}), 500

    @app.route("/api/render/<package_id>", methods=["POST"])
    def api_render_package(package_id: str) -> Response | tuple[Response, int]:
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
            response_data: dict[str, Any] = {
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

    @app.route("/api/kb/sources", methods=["GET"])
    def api_get_kb_sources() -> Response | tuple[Response, int]:
        """API endpoint to get available knowledge base sources."""
        logger = get_crawl_logger()
        try:
            from .services.mcp_service import MCPService

            mcp_service = MCPService()
            # Use thread-safe wrapper to avoid asyncio conflicts
            sources = run_mcp_in_thread(mcp_service.get_available_sources)
            logger.info("Successfully retrieved KB sources from MCP server")

            # Extract sources array from MCP response
            if isinstance(sources, dict) and "sources" in sources:
                return jsonify(sources["sources"])
            elif isinstance(sources, list):
                return jsonify(sources)
            else:
                # Fallback to empty array if unexpected format
                logger.warning(f"Unexpected sources format: {type(sources)}")
                return jsonify([])
        except Exception as e:
            logger.error(f"Failed to get KB sources: {e}")
            return jsonify(
                {
                    "error": "MCP server connection failed",
                    "details": str(e),
                    "suggestion": "Ensure crawl4ai-rag server is running on port 8052",
                }
            ), 500

    @app.route("/api/kb/crawl", methods=["POST"])
    def api_crawl_url() -> Response | tuple[Response, int]:
        """API endpoint to crawl a single URL."""
        logger = get_crawl_logger()
        data = request.get_json()
        if not data or "url" not in data:
            logger.error("Crawl request failed: URL is required")
            return jsonify({"error": "URL is required"}), 400

        url = data["url"]
        logger.info(f"Starting crawl for URL: {url}")

        def crawl_task(url: str) -> None:
            try:
                from .services.mcp_service import MCPService

                # Emit progress start
                socketio.emit(
                    "progress",
                    {"progress": 10, "status": "Connecting to MCP server..."},
                )

                mcp_service = MCPService()

                # Emit progress
                socketio.emit(
                    "progress",
                    {"progress": 30, "status": f"Starting crawl for {url}..."},
                )

                # Perform actual MCP call using thread-safe wrapper
                result = run_mcp_in_thread(mcp_service.crawl_single_page, url)

                # Emit progress
                socketio.emit(
                    "progress",
                    {"progress": 80, "status": "Processing crawl results..."},
                )

                # Emit completion
                socketio.emit(
                    "progress",
                    {"progress": 100, "status": f"Successfully crawled {url}"},
                )
                logger.info(f"Successfully crawled URL: {url}, Result: {result}")

            except Exception as e:
                logger.error(f"Crawl failed for URL {url}: {e}")
                socketio.emit(
                    "progress",
                    {
                        "progress": 100,
                        "status": f"Failed to crawl {url}: {str(e)}",
                        "error": True,
                    },
                )

        socketio.start_background_task(crawl_task, url)
        return jsonify({"message": f"Crawling {url}", "status": "started"})

    @app.route("/api/kb/smart_crawl", methods=["POST"])
    def api_smart_crawl_url() -> Response | tuple[Response, int]:
        """API endpoint to smart crawl a URL."""
        logger = get_crawl_logger()
        data = request.get_json()
        if not data or "url" not in data:
            logger.error("Smart crawl request failed: URL is required")
            return jsonify({"error": "URL is required"}), 400

        url = data["url"]
        max_depth = data.get("max_depth", 3)
        max_concurrent = data.get("max_concurrent", 10)
        chunk_size = data.get("chunk_size", 5000)

        logger.info(
            f"Starting smart crawl for URL: {url} (depth: {max_depth}, concurrent: {max_concurrent}, chunk: {chunk_size})"
        )

        def smart_crawl_task(
            url: str, max_depth: int, max_concurrent: int, chunk_size: int
        ) -> None:
            try:
                from .services.mcp_service import MCPService

                # Emit progress start
                socketio.emit(
                    "progress",
                    {"progress": 10, "status": "Connecting to MCP server..."},
                )

                mcp_service = MCPService()

                # Emit progress
                socketio.emit(
                    "progress",
                    {
                        "progress": 30,
                        "status": f"Starting smart crawl for {url} (depth: {max_depth})...",
                    },
                )

                # Perform actual MCP call using thread-safe wrapper with parameters
                result = run_mcp_in_thread(
                    mcp_service.smart_crawl_url,
                    url,
                    max_depth=max_depth,
                    max_concurrent=max_concurrent,
                    chunk_size=chunk_size,
                )

                # Emit progress
                socketio.emit(
                    "progress",
                    {"progress": 80, "status": "Processing smart crawl results..."},
                )

                # Emit completion
                socketio.emit(
                    "progress",
                    {"progress": 100, "status": f"Successfully smart crawled {url}"},
                )
                logger.info(f"Successfully smart crawled URL: {url}, Result: {result}")

            except Exception as e:
                logger.error(f"Smart crawl failed for URL {url}: {e}")
                socketio.emit(
                    "progress",
                    {
                        "progress": 100,
                        "status": f"Failed to smart crawl {url}: {str(e)}",
                        "error": True,
                    },
                )

        socketio.start_background_task(
            smart_crawl_task, url, max_depth, max_concurrent, chunk_size
        )
        return jsonify(
            {
                "message": f"Smart crawling {url} with depth {max_depth}",
                "status": "started",
                "options": {
                    "max_depth": max_depth,
                    "max_concurrent": max_concurrent,
                    "chunk_size": chunk_size,
                },
            }
        )

    @app.route("/api/kb/parse_github_repository", methods=["POST"])
    def api_parse_github_repository() -> Response | tuple[Response, int]:
        """API endpoint to parse a GitHub repository."""
        logger = get_crawl_logger()
        data = request.get_json()
        if not data or "url" not in data:
            logger.error("GitHub repository parse request failed: URL is required")
            return jsonify({"error": "URL is required"}), 400

        url = data["url"]
        logger.info(f"Starting GitHub repository parse for URL: {url}")

        def parse_github_task(url: str) -> None:
            try:
                from .services.mcp_service import MCPService

                # Emit progress start
                socketio.emit(
                    "progress",
                    {"progress": 10, "status": "Connecting to MCP server..."},
                )

                mcp_service = MCPService()

                # Emit progress
                socketio.emit(
                    "progress",
                    {
                        "progress": 30,
                        "status": f"Starting GitHub repository parse for {url}...",
                    },
                )

                # Perform actual MCP call using thread-safe wrapper
                result = run_mcp_in_thread(mcp_service.parse_github_repository, url)

                # Emit progress
                socketio.emit(
                    "progress",
                    {
                        "progress": 80,
                        "status": "Processing repository parse results...",
                    },
                )

                # Emit completion
                socketio.emit(
                    "progress",
                    {
                        "progress": 100,
                        "status": f"Successfully parsed repository {url}",
                    },
                )
                logger.info(f"Successfully parsed repository: {url}, Result: {result}")

            except Exception as e:
                logger.error(f"Failed to parse repository {url}: {e}")
                socketio.emit(
                    "progress",
                    {
                        "progress": 100,
                        "status": f"Failed to parse repository {url}: {str(e)}",
                        "error": True,
                    },
                )

        socketio.start_background_task(parse_github_task, url)
        return jsonify({"message": f"Parsing repository {url}", "status": "started"})

    @app.route("/api/health/mcp", methods=["GET"])
    def api_health_mcp() -> Response | tuple[Response, int]:
        """API endpoint to check MCP server health."""
        logger = get_crawl_logger()
        try:
            from .services.mcp_service import MCPService

            mcp_service = MCPService()
            health_status = run_mcp_in_thread(mcp_service.check_infrastructure_health)

            logger.info(
                f"MCP health check completed: {health_status['overall']['status']}"
            )

            # Return appropriate HTTP status based on health
            if health_status["overall"]["healthy"]:
                return jsonify(health_status), 200
            elif health_status["overall"]["status"] == "degraded":
                return jsonify(health_status), 206  # Partial Content
            else:
                return jsonify(health_status), 503  # Service Unavailable

        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            error_response = {
                "overall": {
                    "status": "unhealthy",
                    "healthy": False,
                    "message": f"Health check failed: {str(e)}",
                },
                "error": str(e),
            }
            return jsonify(error_response), 503

    @app.route("/api/health/infrastructure", methods=["GET"])
    def api_health_infrastructure() -> Response | tuple[Response, int]:
        """API endpoint to check all infrastructure components."""
        logger = get_crawl_logger()
        try:
            from .services.mcp_service import MCPService

            mcp_service = MCPService()
            health_status = run_mcp_in_thread(mcp_service.check_infrastructure_health)

            # Add additional Flask app health info
            health_status["flask_app"] = {
                "status": "healthy",
                "message": "Flask application responding",
                "timestamp": datetime.now().isoformat(),
            }

            # Add database health info
            try:
                from .database import get_database_service

                db_service = get_database_service()
                session = db_service.get_session()
                session.execute("SELECT 1")
                session.close()
                health_status["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful",
                }
            except Exception as e:
                health_status["database"] = {
                    "status": "unhealthy",
                    "message": f"Database connection failed: {str(e)}",
                }

            # Update overall health with additional components
            healthy_components = sum(
                1
                for component in [
                    "mcp_server",
                    "neo4j",
                    "supabase",
                    "flask_app",
                    "database",
                ]
                if health_status.get(component, {}).get("status") == "healthy"
            )

            total_components = 5
            if healthy_components == total_components:
                health_status["overall"] = {
                    "status": "healthy",
                    "healthy": True,
                    "message": "All infrastructure components are healthy",
                }
                status_code = 200
            elif healthy_components >= 3:
                health_status["overall"] = {
                    "status": "degraded",
                    "healthy": False,
                    "message": f"{healthy_components}/{total_components} infrastructure components are healthy",
                }
                status_code = 206
            else:
                health_status["overall"] = {
                    "status": "unhealthy",
                    "healthy": False,
                    "message": f"Only {healthy_components}/{total_components} infrastructure components are healthy",
                }
                status_code = 503

            logger.info(
                f"Infrastructure health check completed: {health_status['overall']['status']}"
            )
            return jsonify(health_status), status_code

        except Exception as e:
            logger.error(f"Infrastructure health check failed: {e}")
            error_response = {
                "overall": {
                    "status": "unhealthy",
                    "healthy": False,
                    "message": f"Health check failed: {str(e)}",
                },
                "error": str(e),
            }
            return jsonify(error_response), 503

    @app.route("/api/packages", methods=["GET"])
    def api_list_packages() -> Response | tuple[Response, int]:
        """API endpoint to list all packages."""
        try:
            packages = get_all_packages()

            package_list = []
            for package in packages:
                package_data: dict[str, Any] = {
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
    def api_get_package(package_id: str) -> Response | tuple[Response, int]:
        """API endpoint to get a specific package."""
        try:
            package = get_package(package_id)
            if not package:
                return jsonify({"error": "Package not found"}), 404

            package_data: dict[str, Any] = {
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
    def api_get_logs(package_id: str) -> Response | tuple[Response, int]:
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
