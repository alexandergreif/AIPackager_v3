"""CMTrace logging helper for AIPackager v3."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class CMTraceFormatter(logging.Formatter):
    """Custom formatter for CMTrace log format."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in CMTrace format.

        CMTrace format:
        <![LOG[Message]LOG]!><time="HH:MM:SS.fff+000" date="MM-dd-yyyy" component="Component" context="" type="1" thread="1234" file="filename.py:123">

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        # Get timestamp
        dt = datetime.fromtimestamp(record.created)
        time_str = dt.strftime("%H:%M:%S.%f")[:-3] + "+000"  # Milliseconds + timezone
        date_str = dt.strftime("%m-%d-%Y")

        # Get component name (logger name or module name)
        component = getattr(record, "component", record.name)

        # Get context (can be set via extra parameter)
        context = getattr(record, "context", "")

        # Map Python log levels to CMTrace types
        # 1 = Info, 2 = Warning, 3 = Error
        level_map = {
            logging.DEBUG: "1",
            logging.INFO: "1",
            logging.WARNING: "2",
            logging.ERROR: "3",
            logging.CRITICAL: "3",
        }
        log_type = level_map.get(record.levelno, "1")

        # Get thread ID
        thread_id = record.thread or 0

        # Get file and line info
        filename = record.filename or "unknown"
        lineno = record.lineno or 0
        file_info = f"{filename}:{lineno}"

        # Format the message
        message = record.getMessage()

        # Build CMTrace format
        cmtrace_log = (
            f"<![LOG[{message}]LOG]!>"
            f'<time="{time_str}" date="{date_str}" component="{component}" '
            f'context="{context}" type="{log_type}" thread="{thread_id}" file="{file_info}">'
        )

        return cmtrace_log


def setup_cmtrace_logging(
    log_file: Optional[str] = None,
    component: str = "AIPackager",
    level: int = logging.INFO,
    instance_dir: Optional[Path] = None,
) -> logging.Logger:
    """Set up CMTrace logging.

    Args:
        log_file: Path to log file (default: logs/aipackager.log)
        component: Component name for logs
        level: Logging level
        instance_dir: Instance directory for log files

    Returns:
        Configured logger
    """
    # Determine log file path
    if log_file is None:
        if instance_dir:
            log_dir = instance_dir / "logs"
        else:
            log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = str(log_dir / "aipackager.log")

    # Create logger
    logger = logging.getLogger(component)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)

    # Create CMTrace formatter
    formatter = CMTraceFormatter()
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Also add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def get_cmtrace_logger(component: str = "AIPackager") -> logging.Logger:
    """Get or create a CMTrace logger.

    Args:
        component: Component name

    Returns:
        Logger instance
    """
    return logging.getLogger(component)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: str = "",
    component: Optional[str] = None,
) -> None:
    """Log a message with CMTrace context.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        context: Context information
        component: Component name override
    """
    extra = {"context": context}
    if component:
        extra["component"] = component

    logger.log(level, message, extra=extra)


# Convenience functions
def log_info(logger: logging.Logger, message: str, context: str = "") -> None:
    """Log info message with context."""
    log_with_context(logger, logging.INFO, message, context)


def log_warning(logger: logging.Logger, message: str, context: str = "") -> None:
    """Log warning message with context."""
    log_with_context(logger, logging.WARNING, message, context)


def log_error(logger: logging.Logger, message: str, context: str = "") -> None:
    """Log error message with context."""
    log_with_context(logger, logging.ERROR, message, context)


def log_debug(logger: logging.Logger, message: str, context: str = "") -> None:
    """Log debug message with context."""
    log_with_context(logger, logging.DEBUG, message, context)
