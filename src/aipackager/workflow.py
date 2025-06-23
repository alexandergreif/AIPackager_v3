"""
This module defines the PackageRequest class, which encapsulates the business logic
for processing a single package creation request.
"""

import enum
from typing import Any, Dict


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

    def set_step(self, step_name: str) -> None:
        """Sets the current step of the package."""
        import logging

        logger = logging.getLogger("aipackager.workflow")
        old_step = self.package.current_step
        self.package.current_step = step_name
        logger.info(f"{self.package.id} | {old_step} -> {step_name}")

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Saves the extracted metadata to the package."""
        self.package.package_metadata = metadata
