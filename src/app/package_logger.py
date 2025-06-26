"""Per-package logging system for AIPackager v3."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from flask import current_app


class PackageLogger:
    """Handles per-package logging for detailed troubleshooting."""

    def __init__(self, package_id: str):
        self.package_id = package_id
        self.log_file: Optional[Path] = None
        self.logger: Optional[logging.Logger] = None
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up logger for this package."""
        # Create logs directory
        if current_app:
            logs_dir = Path(current_app.instance_path) / "logs"
        else:
            logs_dir = Path("instance/logs")

        logs_dir.mkdir(exist_ok=True)

        # Create log file for this package
        self.log_file = logs_dir / f"{self.package_id}.log"

        # Create logger
        self.logger = logging.getLogger(f"package_{self.package_id}")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.propagate = False  # Don't propagate to root logger

    def log_step(
        self,
        step: str,
        message: str,
        level: str = "INFO",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a step in the package processing pipeline."""
        if not self.logger:
            return

        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "message": message,
            "level": level,
        }

        if data:
            log_entry["data"] = data

        # Log to file
        if level.upper() == "ERROR":
            self.logger.error(f"[{step}] {message}")
            if data:
                self.logger.error(f"[{step}] Data: {json.dumps(data, indent=2)}")
        elif level.upper() == "WARNING":
            self.logger.warning(f"[{step}] {message}")
            if data:
                self.logger.warning(f"[{step}] Data: {json.dumps(data, indent=2)}")
        else:
            self.logger.info(f"[{step}] {message}")
            if data:
                self.logger.debug(f"[{step}] Data: {json.dumps(data, indent=2)}")

    def log_error(
        self, step: str, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error with full context."""
        error_data: Dict[str, Any] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "step": step,
        }

        if context:
            error_data["context"] = context

        self.log_step(step, f"ERROR: {error}", "ERROR", error_data)

    def log_5_stage_pipeline(
        self,
        stage: int,
        stage_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log 5-stage pipeline progress."""
        message = f"Stage {stage} ({stage_name}): {status}"
        self.log_step(f"PIPELINE_STAGE_{stage}", message, "INFO", details)

    def get_logs(self) -> str:
        """Get all logs for this package."""
        if self.log_file and self.log_file.exists():
            return self.log_file.read_text()
        return "No logs available"

    def get_log_file_path(self) -> Optional[Path]:
        """Get the path to the log file."""
        return self.log_file if self.log_file and self.log_file.exists() else None


def get_package_logger(package_id: str) -> PackageLogger:
    """Get or create a logger for a specific package."""
    return PackageLogger(package_id)
