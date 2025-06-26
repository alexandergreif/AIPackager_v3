"""Tests for the PackageRequest workflow class."""

from unittest.mock import MagicMock
from src.aipackager.workflow import PackageRequest


def test_package_request_instantiation():
    """Test that PackageRequest can be instantiated."""
    mock_package_row = MagicMock()
    package_request = PackageRequest(mock_package_row)
    assert package_request.package == mock_package_row


def test_start_method():
    """Test the start method."""
    mock_package_row = MagicMock()
    mock_package_row.status = "uploading"
    package_request = PackageRequest(mock_package_row)
    package_request.start()
    assert mock_package_row.status == "processing"


def test_set_step_method():
    """Test the set_step method."""
    mock_package_row = MagicMock()
    mock_package_row.current_step = "uploading"
    package_request = PackageRequest(mock_package_row)
    package_request.set_step("extracting_metadata")
    assert mock_package_row.current_step == "extracting_metadata"


def test_set_step_logging(tmp_path):
    """Test that set_step logs to the correct file."""
    import logging
    from src.app.logging_cmtrace import CMTraceFormatter

    log_file = tmp_path / "packages.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(CMTraceFormatter())

    logger = logging.getLogger("aipackager.workflow")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    mock_package_row = MagicMock()
    mock_package_row.id = "1234"
    mock_package_row.current_step = "uploading"

    package_request = PackageRequest(mock_package_row)
    package_request.set_step("extracting_metadata")

    with open(log_file, "r") as f:
        log_content = f.read()

    assert "1234" in log_content
    assert "uploading -> extracting_metadata" in log_content


def test_save_metadata_method():
    """Test the save_metadata method."""
    mock_package_row = MagicMock()
    package_request = PackageRequest(mock_package_row)
    metadata = {"product_name": "Test Product"}
    package_request.save_metadata(metadata)
    assert mock_package_row.package_metadata == metadata



def test_save_metadata_persists_to_db(tmp_path):
    """save_metadata should create a Metadata record linked to the package."""
    from src.app import create_app
    from src.app.database import get_database_service, create_package, get_package

    db_path = tmp_path / "test.db"
    app = create_app({"DATABASE_URL": f"sqlite:///{db_path}"})

    with app.app_context():
        db_service = get_database_service()
        db_service.create_tables()

        package = create_package(
            filename="test.msi", file_path="/tmp/test.msi"
        )

        package_request = PackageRequest(package)
        package_request.save_metadata({"product_name": "Test Product"})

        refreshed = get_package(str(package.id))
        assert refreshed is not None
        assert refreshed.package_metadata is not None
        assert refreshed.package_metadata.product_name == "Test Product"

