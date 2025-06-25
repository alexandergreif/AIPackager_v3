"""Mock progress poller for AIPackager v3."""

from typing import Dict, Any
from uuid import uuid4

_JOBS: Dict[str, Dict[str, Any]] = {}


def get_job(job_id: str) -> Dict[str, Any] | None:
    """Get a job by its ID."""
    return _JOBS.get(job_id)


def set_job_progress(job_id: str, progress: int, status: str = "Processing") -> None:
    """Set the progress of a job."""
    job = _JOBS.get(job_id)
    if job:
        job["progress"] = progress
        job["status"] = status


def start_job(filename: str, custom_instructions: str | None = None) -> str:
    """Start a job and return its ID."""
    job_id = str(uuid4())
    _JOBS[job_id] = {
        "filename": filename,
        "custom_instructions": custom_instructions or "",
        "status": "Uploading",
        "progress": 0,
    }
    return job_id
