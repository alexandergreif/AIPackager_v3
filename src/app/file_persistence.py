"""File persistence utilities for AIPackager v3."""

import os
from pathlib import Path
from typing import Tuple
from uuid import UUID, uuid4
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def save_uploaded_file(file: FileStorage, instance_dir: Path) -> Tuple[UUID, str]:
    """Save an uploaded file with UUID naming.

    Args:
        file: The uploaded file from Flask request
        instance_dir: Path to the instance directory

    Returns:
        Tuple of (file_id, file_path) where file_id is the generated UUID
        and file_path is the absolute path to the saved file
    """
    # Generate unique file ID
    file_id = uuid4()

    # Secure the filename to prevent directory traversal
    secure_name = secure_filename(file.filename or "unknown")

    # Create filename with UUID prefix
    filename = f"{file_id}_{secure_name}"

    # Ensure uploads directory exists
    uploads_dir = instance_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    # Full file path
    file_path = uploads_dir / filename

    # Save the file
    file.save(str(file_path))

    return file_id, str(file_path)


def get_file_path(file_id: UUID, filename: str, instance_dir: Path) -> str:
    """Get the file path for a given UUID and filename.

    Args:
        file_id: The UUID of the file
        filename: The original filename
        instance_dir: Path to the instance directory

    Returns:
        The absolute path to the file
    """
    secure_name = secure_filename(filename)
    filename_with_uuid = f"{file_id}_{secure_name}"
    file_path = instance_dir / "uploads" / filename_with_uuid
    return str(file_path)


def delete_file(file_path: str) -> bool:
    """Delete a file from the filesystem.

    Args:
        file_path: Absolute path to the file to delete

    Returns:
        True if file was successfully deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except OSError:
        return False


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes.

    Args:
        file_path: Absolute path to the file

    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def file_exists(file_path: str) -> bool:
    """Check if a file exists.

    Args:
        file_path: Absolute path to the file

    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)
