"""Tests for SP1-04: Mock progress poller."""

from src.app import create_app
from src.app.progress import get_job, set_job_progress, start_job


def test_start_job_creates_new_job():
    """Test that start_job creates a new job with initial state."""
    job_id = start_job("test.msi")
    job = get_job(job_id)

    assert job is not None
    assert job["filename"] == "test.msi"
    assert job["status"] == "Uploading"
    assert job["progress"] == 0


def test_set_job_progress_updates_job():
    """Test that set_job_progress updates the progress and status of a job."""
    job_id = start_job("test.msi")
    set_job_progress(job_id, 50, "Parsing")
    job = get_job(job_id)

    assert job["progress"] == 50
    assert job["status"] == "Parsing"


def test_get_job_returns_none_for_invalid_id():
    """Test that get_job returns None for an invalid job ID."""
    job = get_job("invalid-id")
    assert job is None


def test_progress_route_returns_json():
    """Test that the /progress/<id> route returns JSON data."""
    app = create_app()
    client = app.test_client()

    job_id = start_job("test.msi")
    response = client.get(
        f"/progress/{job_id}", headers={"X-Requested-With": "XMLHttpRequest"}
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["job_id"] == job_id
    assert data["progress"] == 0
    assert data["status"] == "Uploading"


def test_progress_polling_updates_ui():
    """Test that the UI can poll for progress updates."""
    app = create_app()
    client = app.test_client()

    job_id = start_job("test.msi")

    headers = {"X-Requested-With": "XMLHttpRequest"}

    # Stage 1: Uploading
    response = client.get(f"/progress/{job_id}", headers=headers)
    assert response.get_json()["progress"] == 0

    # Stage 2: Parsing
    set_job_progress(job_id, 33, "Parsing")
    response = client.get(f"/progress/{job_id}", headers=headers)
    assert response.get_json()["progress"] == 33

    # Stage 3: Generating
    set_job_progress(job_id, 66, "Generating")
    response = client.get(f"/progress/{job_id}", headers=headers)
    assert response.get_json()["progress"] == 66

    # Stage 4: Complete
    set_job_progress(job_id, 100, "Complete")
    response = client.get(f"/progress/{job_id}", headers=headers)
    assert response.get_json()["progress"] == 100


def test_progress_page_loads_with_job_id():
    """Test that the progress.html page loads with the correct job ID."""
    app = create_app()
    client = app.test_client()

    job_id = start_job("test.msi")
    response = client.get(f"/progress/{job_id}")

    assert response.status_code == 200
    assert job_id.encode() in response.data
