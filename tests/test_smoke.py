"""Tests for SP1-05: Smoke tests for all routes."""

from io import BytesIO


def test_upload_flow(client):
    """Test the full upload flow, from upload to detail page."""
    # 1. Upload a dummy file
    data = {"installer": (BytesIO(b"my file contents"), "test.msi")}
    response = client.post("/upload", data=data, content_type="multipart/form-data")

    # 2. Follow the redirect to the progress page
    assert response.status_code == 302
    progress_url = response.headers["Location"]
    assert "/progress/" in progress_url

    # 3. Check the progress page
    response = client.get(progress_url)
    assert response.status_code == 200
    assert b"Processing Progress" in response.data

    # 4. Check the detail page (mocking progress completion)
    job_id = progress_url.split("/")[-1]
    detail_url = f"/detail/{job_id}"
    response = client.get(detail_url)
    assert response.status_code == 200
    assert b"Job Details" in response.data


def test_history_page_loads(client):
    """Test that the history page loads correctly."""
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Upload History" in response.data


def test_invalid_job_id_returns_404(client):
    """Test that an invalid job ID returns a 404 error."""
    response = client.get("/progress/invalid-id")
    assert response.status_code == 404

    response = client.get("/detail/invalid-id")
    assert response.status_code == 404
