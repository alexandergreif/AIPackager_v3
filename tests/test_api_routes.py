"""Tests for API routes."""

import json
import tempfile
from io import BytesIO
import pytest

from src.app import create_app
from src.app.database import get_database_service, get_package


@pytest.fixture
def app():
    """Create Flask app for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app = create_app()
        app.config["TESTING"] = True
        app.instance_path = temp_dir

        with app.app_context():
            # Initialize database
            db_service = get_database_service()
            db_service.create_tables()

        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_file():
    """Create a sample file for testing."""
    return (BytesIO(b"Sample MSI content"), "test_installer.msi")


class TestAPIRoutes:
    """Test API route functionality."""

    def test_api_create_package_success(self, client, sample_file):
        """Test successful package creation via API."""
        data = {"installer": sample_file, "custom_instructions": "Test instructions"}

        response = client.post("/api/packages", data=data)

        assert response.status_code == 200

        json_data = response.get_json()
        assert "package_id" in json_data
        assert json_data["filename"] == "test_installer.msi"
        assert json_data["status"] == "uploading"
        assert json_data["custom_instructions"] == "Test instructions"
        assert "upload_time" in json_data

    def test_api_create_package_no_file(self, client):
        """Test package creation without file."""
        response = client.post("/api/packages", data={})

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["error"] == "No file part"

    def test_api_create_package_empty_filename(self, client):
        """Test package creation with empty filename."""
        data = {"installer": (BytesIO(b"content"), "")}

        response = client.post("/api/packages", data=data)

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["error"] == "No selected file"

    def test_api_list_packages_empty(self, client):
        """Test listing packages when none exist."""
        response = client.get("/api/packages")

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["packages"] == []

    def test_api_list_packages_with_data(self, client, sample_file):
        """Test listing packages with existing data."""
        # First create a package
        data = {"installer": sample_file, "custom_instructions": "Test instructions"}
        create_response = client.post("/api/packages", data=data)
        assert create_response.status_code == 200

        # Then list packages
        response = client.get("/api/packages")

        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data["packages"]) == 1

        package = json_data["packages"][0]
        assert package["filename"] == "test_installer.msi"
        assert package["status"] == "uploading"
        assert package["custom_instructions"] == "Test instructions"

    def test_api_get_package_success(self, client, sample_file):
        """Test getting a specific package."""
        # First create a package
        data = {"installer": sample_file, "custom_instructions": "Test instructions"}
        create_response = client.post("/api/packages", data=data)
        package_id = create_response.get_json()["package_id"]

        # Then get the package
        response = client.get(f"/api/packages/{package_id}")

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["package_id"] == package_id
        assert json_data["filename"] == "test_installer.msi"
        assert json_data["status"] == "uploading"
        assert json_data["custom_instructions"] == "Test instructions"

    def test_api_get_package_not_found(self, client):
        """Test getting a non-existent package."""
        fake_id = "12345678-1234-5678-9012-123456789abc"
        response = client.get(f"/api/packages/{fake_id}")

        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data["error"] == "Package not found"

    def test_api_create_package_with_different_file_types(self, client):
        """Test creating packages with different file types."""
        test_files = [
            (BytesIO(b"EXE content"), "installer.exe"),
            (BytesIO(b"MSI content"), "setup.msi"),
            (BytesIO(b"ZIP content"), "package.zip"),
        ]

        for file_content, filename in test_files:
            data = {
                "installer": (file_content, filename),
                "custom_instructions": f"Instructions for {filename}",
            }

            response = client.post("/api/packages", data=data)

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data["filename"] == filename
            assert json_data["custom_instructions"] == f"Instructions for {filename}"

    def test_api_create_package_without_custom_instructions(self, client, sample_file):
        """Test creating package without custom instructions."""
        data = {"installer": sample_file}

        response = client.post("/api/packages", data=data)

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["custom_instructions"] == ""

    def test_api_create_large_file(self, client):
        """Test creating package with larger file."""
        # Create 1MB file
        large_content = b"A" * (1024 * 1024)
        data = {
            "installer": (BytesIO(large_content), "large_installer.msi"),
            "custom_instructions": "Large file test",
        }

        response = client.post("/api/packages", data=data)

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["filename"] == "large_installer.msi"

    def test_api_packages_content_type(self, client, sample_file):
        """Test that API returns proper JSON content type."""
        data = {"installer": sample_file, "custom_instructions": "Test instructions"}

        response = client.post("/api/packages", data=data)

        assert response.status_code == 200
        assert response.content_type == "application/json"

        # Test GET endpoints too
        response = client.get("/api/packages")
        assert response.content_type == "application/json"

        package_id = (
            json.loads(response.data)["packages"][0]["package_id"]
            if json.loads(response.data)["packages"]
            else None
        )
        if package_id:
            response = client.get(f"/api/packages/{package_id}")
            assert response.content_type == "application/json"

    def test_api_upload_extracts_metadata(self, client, sample_file):
        """Test that metadata is extracted and stored on upload."""
        data = {"installer": sample_file, "custom_instructions": "Test instructions"}

        response = client.post("/api/packages", data=data)
        assert response.status_code == 200
        package_id = response.get_json()["package_id"]

        # Retrieve the package from the database to check metadata
        with client.application.app_context():
            package = get_package(package_id)

        assert package is not None
        assert package.package_metadata is not None

        # The metadata attribute of the Metadata object is already a dictionary
        metadata = package.package_metadata

        assert package.filename == "test_installer.msi"
        assert (
            metadata.product_name is None
        )  # We don't have a real MSI, so this should be None
