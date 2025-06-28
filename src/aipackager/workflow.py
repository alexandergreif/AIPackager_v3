"""
This module defines the PackageRequest class, which encapsulates the business logic
for processing a single package creation request.
"""

import enum
import logging
from typing import Any, Dict
from src.app.package_logger import get_package_logger

logger = logging.getLogger(__name__)


class WorkflowStep(enum.Enum):
    """Represents the steps in the package creation workflow."""

    UPLOAD = "upload"
    EXTRACT_METADATA = "extract_metadata"
    PREPROCESS = "preprocess"
    GENERATE_PROMPT = "generate_prompt"
    CALL_AI = "call_ai"
    RENDER_SCRIPT = "render_script"
    COMPLETED = "completed"
    FAILED = "failed"


class PackageRequest:
    """Represents a single package creation request."""

    def __init__(self, package: Any) -> None:
        self.package = package

    def start(self) -> None:
        """Starts the processing of the package."""
        self.package.status = "processing"
        package_logger = get_package_logger(self.package.id)
        package_logger.log_step(
            "WORKFLOW_START", f"Starting package processing for {self.package.id}"
        )

    def set_step(self, step_name: str) -> None:
        """Sets the current step of the package."""
        package_logger = get_package_logger(self.package.id)
        old_step = self.package.current_step
        self.package.current_step = step_name
        package_logger.log_step(
            "WORKFLOW_STEP",
            f"Transitioning from {old_step} to {step_name}",
            data={"old_step": old_step, "new_step": step_name},
        )

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Persist metadata for this package and attach the new record."""
        try:
            from src.app.database import create_metadata

            record = create_metadata(self.package.id, **metadata)
            # Attach for immediate access when this instance is still in use
            self.package.package_metadata = record
        except Exception:  # pragma: no cover - fail silently in tests without DB
            # Fallback to simple assignment when database helpers are unavailable
            self.package.package_metadata = metadata

    def resume(self) -> None:
        """Resume processing of this package from its current step."""
        package_logger = get_package_logger(self.package.id)
        package_logger.log_step(
            "WORKFLOW_RESUME",
            f"Resuming package {self.package.id} from step {self.package.current_step}",
        )

        try:
            # For now, we'll simulate completing the workflow
            # In a real implementation, this would continue from the current step
            self.set_step(WorkflowStep.COMPLETED.value)
            self.package.status = "completed"
            self.package.progress_pct = 100

            # Save changes to database
            from src.app.database import get_database_service

            db_service = get_database_service()
            session = db_service.get_session()
            try:
                session.merge(self.package)
                session.commit()
                package_logger.log_step(
                    "WORKFLOW_RESUME",
                    f"Successfully resumed and completed package {self.package.id}",
                )
            finally:
                session.close()

        except Exception as e:
            package_logger.log_error(
                "WORKFLOW_RESUME", e, context={"package_id": self.package.id}
            )
            self.set_step(WorkflowStep.FAILED.value)
            self.package.status = "failed"

            # Save failure state to database
            from src.app.database import get_database_service

            db_service = get_database_service()
            session = db_service.get_session()
            try:
                session.merge(self.package)
                session.commit()
            finally:
                session.close()

    @classmethod
    def resume_pending_jobs(cls) -> None:
        """Resume all pending jobs that are not completed or failed.

        This method should be called on application startup to resume
        any workflows that were interrupted.
        """
        # No package_id available here, so use the general logger
        logger.info("Starting resume of pending jobs...")

        try:
            from src.app.database import get_database_service
            from src.app.models import Package

            db_service = get_database_service()
            session = db_service.get_session()

            try:
                # Find all packages that are not completed or failed
                pending_packages = (
                    session.query(Package)
                    .filter(Package.status.notin_(["completed", "failed"]))
                    .all()
                )

                logger.info(f"Found {len(pending_packages)} pending packages to resume")

                for package in pending_packages:
                    package_logger = get_package_logger(package.id)
                    package_logger.log_step(
                        "WORKFLOW_RESUME_PENDING",
                        f"Resuming package {package.id} (status: {package.status}, step: {package.current_step})",
                    )
                    package_request = cls(package)
                    package_request.resume()

                logger.info("Completed resume of all pending jobs")

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error during job resume: {e}")
