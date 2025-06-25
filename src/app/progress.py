"""Mock progress poller for AIPackager v3."""

from typing import Dict, Any


def get_job(job_id: str) -> Dict[str, Any] | None:
    """Get a job by its ID."""
    # This is a mock implementation. In a real application, this would
    # query a database or a job queue.
    return None


def set_job_progress(job_id: str, progress: int) -> None:
    """Set the progress of a job."""
    # This is a mock implementation. In a real application, this would
    # update the job progress in a database or job queue.
    pass


def start_job(job_id: str, job_type: str = "script_generation") -> None:
    """Start a job."""
    # This is a mock implementation. In a real application, this would
    # create and start a job in a job queue.
    pass
