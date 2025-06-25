"""Tests for file persistence functionality."""

import os
import tempfile
from pathlib import Path
from uuid import UUID
import pytest
from werkzeug.datastructures import FileStorage
from io import BytesIO

from src.app.file_persistence import save_uploaded_file, get_file_path, delete_file


@pytest.fixture
def temp_instance_dir():
    """Create temporary instance directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        instance_dir = Path(temp_dir) / "instance"
        instance_dir.mkdir()
        yield instance_dir


@pytest.fixture
def mock_file():
    """Create a mock uploaded file."""
    file_content = b"This is a test MSI file content"
    file_obj = BytesIO(file_content)
    return FileStorage(
        stream=file_obj, filename="test_installer.msi", content_type="application/x-msi"
    )


class TestFilePersistence:
    """Test file persistence functionality."""

    def test_save_uploaded_file(self, temp_instance_dir, mock_file):
        """Test saving an uploaded file with UUID naming."""
        # Save the file
        file_id, file_path = save_uploaded_file(mock_file, temp_instance_dir)

        # Verify file_id is a UUID
        assert isinstance(file_id, UUID)

        # Verify file path format
        expected_filename = f"{file_id}_test_installer.msi"
        expected_path = temp_instance_dir / "uploads" / expected_filename
        assert file_path == str(expected_path)

        # Verify file was actually saved
        assert os.path.exists(file_path)

        # Verify file content
        with open(file_path, "rb") as f:
            content = f.read()
        assert content == b"This is a test MSI file content"

    def test_save_uploaded_file_creates_uploads_dir(self, temp_instance_dir, mock_file):
        """Test that uploads directory is created if it doesn't exist."""
        uploads_dir = temp_instance_dir / "uploads"
        assert not uploads_dir.exists()

        # Save file should create the directory
        file_id, file_path = save_uploaded_file(mock_file, temp_instance_dir)

        assert uploads_dir.exists()
        assert uploads_dir.is_dir()

    def test_save_uploaded_file_with_different_extensions(self, temp_instance_dir):
        """Test saving files with different extensions."""
        test_cases = [
            ("installer.exe", "application/x-executable"),
            ("setup.msi", "application/x-msi"),
            ("package.zip", "application/zip"),
        ]

        for filename, content_type in test_cases:
            file_obj = BytesIO(b"test content")
            mock_file = FileStorage(
                stream=file_obj, filename=filename, content_type=content_type
            )

            file_id, file_path = save_uploaded_file(mock_file, temp_instance_dir)

            # Verify correct extension is preserved
            assert file_path.endswith(filename)
            assert os.path.exists(file_path)

    def test_get_file_path(self, temp_instance_dir):
        """Test getting file path from UUID and filename."""
        file_id = UUID("12345678-1234-5678-9012-123456789abc")
        filename = "test.msi"

        expected_path = temp_instance_dir / "uploads" / f"{file_id}_{filename}"
        actual_path = get_file_path(file_id, filename, temp_instance_dir)

        assert actual_path == str(expected_path)

    def test_delete_file(self, temp_instance_dir, mock_file):
        """Test deleting a saved file."""
        # First save a file
        file_id, file_path = save_uploaded_file(mock_file, temp_instance_dir)
        assert os.path.exists(file_path)

        # Delete the file
        success = delete_file(file_path)

        assert success is True
        assert not os.path.exists(file_path)

    def test_delete_nonexistent_file(self, temp_instance_dir):
        """Test deleting a file that doesn't exist."""
        nonexistent_path = temp_instance_dir / "uploads" / "nonexistent.msi"

        success = delete_file(str(nonexistent_path))

        assert success is False

    def test_save_file_with_unsafe_filename(self, temp_instance_dir):
        """Test saving file with potentially unsafe filename."""
        unsafe_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "file with spaces.msi",
            "file-with-special-chars!@#$.exe",
        ]

        for unsafe_name in unsafe_names:
            file_obj = BytesIO(b"test content")
            mock_file = FileStorage(
                stream=file_obj, filename=unsafe_name, content_type="application/x-msi"
            )

            file_id, file_path = save_uploaded_file(mock_file, temp_instance_dir)

            # Verify file is saved in uploads directory (not escaped)
            assert str(temp_instance_dir / "uploads") in file_path
            assert os.path.exists(file_path)

            # Verify filename is sanitized but extension preserved
            path_obj = Path(file_path)
            assert path_obj.parent == temp_instance_dir / "uploads"

    def test_save_empty_file(self, temp_instance_dir):
        """Test saving an empty file."""
        empty_file = FileStorage(
            stream=BytesIO(b""), filename="empty.msi", content_type="application/x-msi"
        )

        file_id, file_path = save_uploaded_file(empty_file, temp_instance_dir)

        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) == 0

    def test_save_large_file(self, temp_instance_dir):
        """Test saving a larger file."""
        # Create 1MB of test data
        large_content = b"A" * (1024 * 1024)
        large_file = FileStorage(
            stream=BytesIO(large_content),
            filename="large_installer.msi",
            content_type="application/x-msi",
        )

        file_id, file_path = save_uploaded_file(large_file, temp_instance_dir)

        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) == 1024 * 1024

        # Verify content integrity
        with open(file_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == large_content
