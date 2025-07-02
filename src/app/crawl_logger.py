import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_crawl_logger() -> logging.Logger:
    """Get a logger for crawl operations."""
    log_dir = Path("instance/logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "crawl4ai.log"

    logger = logging.getLogger("crawl4ai")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(log_file, maxBytes=10240000, backupCount=10)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
