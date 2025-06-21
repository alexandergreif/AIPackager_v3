"""Tests for SP1-01: Flask app factory + routes."""

from flask import Flask

from src.app import create_app


def test_create_app_returns_flask_instance():
    """Test that create_app returns a Flask application instance."""
    app = create_app()
    assert isinstance(app, Flask)
    assert app.name == "src.app"


def test_app_has_required_routes():
    """Test that all required routes are registered."""
    app = create_app()

    # Get all registered routes
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    # Check required routes exist
    assert "/upload" in routes
    assert "/progress/<id>" in routes
    assert "/detail/<id>" in routes
    assert "/history" in routes


def test_upload_route_returns_200():
    """Test that /upload route returns HTTP 200."""
    app = create_app()
    client = app.test_client()

    response = client.get("/upload")
    assert response.status_code == 200
    assert b"upload" in response.data.lower()


def test_progress_route_returns_200():
    """Test that /progress/<id> route returns HTTP 200."""
    app = create_app()
    client = app.test_client()

    response = client.get("/progress/test-id")
    assert response.status_code == 200
    assert b"progress" in response.data.lower()


def test_detail_route_returns_200():
    """Test that /detail/<id> route returns HTTP 200."""
    app = create_app()
    client = app.test_client()

    response = client.get("/detail/test-id")
    assert response.status_code == 200
    assert b"detail" in response.data.lower()


def test_history_route_returns_200():
    """Test that /history route returns HTTP 200."""
    app = create_app()
    client = app.test_client()

    response = client.get("/history")
    assert response.status_code == 200
    assert b"history" in response.data.lower()


def test_app_config_is_testing():
    """Test that app can be configured for testing."""
    app = create_app({"TESTING": True})
    assert app.config["TESTING"] is True


def test_all_routes_return_html_content():
    """Test that all routes return HTML-like content."""
    app = create_app()
    client = app.test_client()

    routes_to_test = ["/upload", "/progress/test-id", "/detail/test-id", "/history"]

    for route in routes_to_test:
        response = client.get(route)
        assert response.status_code == 200
        # Check that response looks like HTML (contains angle brackets)
        assert b"<" in response.data and b">" in response.data
