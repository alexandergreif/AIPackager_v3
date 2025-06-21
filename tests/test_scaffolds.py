"""Tests for SP1-03: Scaffold HTML templates."""

from flask import render_template

from src.app import create_app


def test_upload_template_renders():
    """Test that upload.html template renders."""
    app = create_app()
    with app.app_context():
        rendered = render_template("upload.html")
        assert "Upload Installer" in rendered
        assert "file" in rendered


def test_progress_template_renders():
    """Test that progress.html template renders."""
    app = create_app()
    with app.app_context():
        rendered = render_template("progress.html", job_id="test-id")
        assert "Processing Progress" in rendered
        assert "test-id" in rendered


def test_detail_template_renders():
    """Test that detail.html template renders."""
    app = create_app()
    with app.app_context():
        rendered = render_template("detail.html", job_id="test-id")
        assert "Job Details" in rendered
        assert "test-id" in rendered


def test_history_template_renders():
    """Test that history.html template renders."""
    app = create_app()
    with app.app_context():
        rendered = render_template("history.html")
        assert "Upload History" in rendered
        assert "Job ID" in rendered
