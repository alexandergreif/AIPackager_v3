"""Mock progress poller for AIPackager v3."""

import uuid
from typing import Dict, Any

# In-memory storage for jobs
_jobs: Dict[str, Dict[str, Any]] = {}


def start_job(filename: str, custom_instructions: str = "") -> str:
    """Create a new job and return its ID."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "filename": filename,
        "custom_instructions": custom_instructions,
        "status": "Uploading",
        "progress": 0,
    }
    return job_id


def set_job_progress(job_id: str, progress: int, status: str) -> None:
    """Update the progress and status of a job."""
    if job_id in _jobs:
        _jobs[job_id]["progress"] = progress
        _jobs[job_id]["status"] = status


def get_job(job_id: str) -> Dict[str, Any] | None:
    """Get a job by its ID."""
    return _jobs.get(job_id)
