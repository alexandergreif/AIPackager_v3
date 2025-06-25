"""Tests for SP1-02: Sidebar layout + dark mode templates."""

from flask import render_template_string

from src.app import create_app
from src.app.progress import start_job


def test_base_template_exists():
    """Test that base template can be rendered."""
    app = create_app()

    with app.app_context():
        # Try to render base template with minimal content
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}Test{% endblock %}"
        )
        assert "Test" in rendered


def test_base_template_has_tailwind():
    """Test that base template includes Tailwind CSS."""
    app = create_app()

    with app.app_context():
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}{% endblock %}"
        )
        # Check for Tailwind CDN
        assert "tailwindcss.com" in rendered
        # Check for TODO comment about npm build
        assert "Replace with npm/tailwindcss build in Sprint 3" in rendered


def test_base_template_has_alpine():
    """Test that base template includes Alpine.js."""
    app = create_app()

    with app.app_context():
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}{% endblock %}"
        )
        # Check for Alpine.js CDN
        assert "alpinejs" in rendered.lower()


def test_base_template_has_sidebar():
    """Test that base template includes sidebar navigation."""
    app = create_app()

    with app.app_context():
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}{% endblock %}"
        )
        # Check for navigation links
        assert "/upload" in rendered
        assert "/history" in rendered
        # Check for sidebar structure
        assert "sidebar" in rendered.lower() or "nav" in rendered.lower()


def test_base_template_has_dark_mode_toggle():
    """Test that base template includes dark mode toggle."""
    app = create_app()

    with app.app_context():
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}{% endblock %}"
        )
        # Check for dark mode toggle elements
        assert "dark" in rendered.lower()
        assert "toggle" in rendered.lower() or "switch" in rendered.lower()


def test_base_template_responsive():
    """Test that base template has responsive design classes."""
    app = create_app()

    with app.app_context():
        rendered = render_template_string(
            "{% extends 'base.html' %}{% block content %}{% endblock %}"
        )
        # Check for responsive Tailwind classes
        assert any(cls in rendered for cls in ["md:", "lg:", "sm:", "xl:"])


def test_template_inheritance_structure():
    """Test that template inheritance works properly."""
    app = create_app()

    with app.app_context():
        # Test that we can extend base and override blocks
        rendered = render_template_string(
            """
            {% extends 'base.html' %}
            {% block title %}Custom Title{% endblock %}
            {% block content %}Custom Content{% endblock %}
        """
        )
        assert "Custom Title" in rendered
        assert "Custom Content" in rendered


def test_routes_use_templates():
    """Test that routes can render templates."""
    app = create_app()
    client = app.test_client()

    job_id = start_job("test.msi")
    routes_to_test = {
        "/upload": b"Upload Installer",
        f"/progress/{job_id}": b"Processing Progress",
        f"/detail/{job_id}": b"Job Details",
        "/history": b"Upload History",
    }

    for route, expected_content in routes_to_test.items():
        response = client.get(route)
        assert response.status_code == 200
        assert expected_content in response.data
