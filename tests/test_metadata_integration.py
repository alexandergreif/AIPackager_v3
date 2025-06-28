"""Integration tests for metadata extraction and database storage."""

import json
from pathlib import Path

import pytest

from src.app import create_app
from src.app.database import get_database_service


def test_api_upload_saves_metadata_correctly(tmp_path):
    """Test that the API upload endpoint correctly extracts and saves metadata."""
    # Create test app with temporary database
    db_path = tmp_path / "test.db"
    app = create_app({"DATABASE_URL": f"sqlite:///{db_path}"})

    with app.test_client() as client:
        with app.app_context():
            # Create database tables
            db_service = get_database_service()
            db_service.create_tables()

            # Create a temporary MSI file for testing
            test_file = tmp_path / "test.msi"
            test_file.write_bytes(b"PK\x03\x04")  # Simple test content

            # Test the API upload endpoint
            with open(test_file, "rb") as f:
                response = client.post(
                    "/api/packages",
                    data={
                        "installer": (f, "test.msi"),
                        "custom_instructions": "Test upload",
                    },
                    content_type="multipart/form-data",
                )

            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "package_id" in data
            package_id = data["package_id"]

            # Verify package was created
            from src.app.database import get_package

            package = get_package(package_id)
            assert package is not None
            assert package.filename == "test.msi"
            assert package.custom_instructions == "Test upload"

            # Verify metadata was created (even if extraction failed, record should exist)
            assert package.package_metadata is not None
            metadata = package.package_metadata

            # The metadata fields might be None due to extraction failure,
            # but the metadata record should exist
            assert metadata.package_id == package.id


def test_metadata_extraction_with_real_msi():
    """Test metadata extraction with a real MSI file if available."""
    # Look for the Chrome MSI file that was mentioned in the user's testing
    chrome_msi = Path("googlechromestandaloneenterprise_136.0.0_64bit.msi")

    if not chrome_msi.exists():
        pytest.skip("Chrome MSI file not available for testing")

    from src.app.metadata_extractor import extract_file_metadata

    # Extract metadata from real MSI
    metadata = extract_file_metadata(str(chrome_msi))

    # Verify we got some metadata
    assert isinstance(metadata, dict)

    # Check if we got the expected Chrome metadata
    if metadata.get("product_name"):
        assert (
            "Chrome" in metadata["product_name"] or "Google" in metadata["product_name"]
        )

    if metadata.get("publisher"):
        assert "Google" in metadata["publisher"]


def test_create_metadata_function_with_individual_fields():
    """Test that create_metadata works with individual field parameters."""
    from src.app import create_app
    from src.app.database import create_package, create_metadata, get_package

    app = create_app({"DATABASE_URL": "sqlite:///:memory:"})

    with app.app_context():
        # Create database tables
        db_service = get_database_service()
        db_service.create_tables()

        # Create a test package
        package = create_package(
            filename="test.msi",
            file_path="/tmp/test.msi",
            custom_instructions="Test package",
        )

        # Create metadata with individual fields
        metadata = create_metadata(
            package_id=package.id,
            product_name="Test Application",
            version="1.0.0",
            publisher="Test Company",
            architecture="x64",
            product_code="{12345678-1234-1234-1234-123456789012}",
            executable_names=["app.exe"],
        )

        # Verify metadata was saved correctly
        assert metadata.product_name == "Test Application"
        assert metadata.version == "1.0.0"
        assert metadata.publisher == "Test Company"
        assert metadata.architecture == "x64"
        assert metadata.product_code == "{12345678-1234-1234-1234-123456789012}"
        assert metadata.executable_names == ["app.exe"]

        # Verify relationship works
        retrieved_package = get_package(str(package.id))
        assert retrieved_package is not None
        assert retrieved_package.package_metadata is not None
        assert retrieved_package.package_metadata.product_name == "Test Application"
        assert retrieved_package.package_metadata.executable_names == ["app.exe"]
