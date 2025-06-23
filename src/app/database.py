"""Database service for AIPackager v3."""

from pathlib import Path
from typing import Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from flask import current_app

from .models import Base, Package, Metadata


class DatabaseService:
    """Service for database operations."""

    def __init__(self, database_url: str):
        """Initialize database service.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)


def get_database_service() -> DatabaseService:
    """Get the database service instance."""
    if not hasattr(current_app, "database_service"):
        # Get instance directory
        instance_dir = Path(current_app.instance_path)
        instance_dir.mkdir(exist_ok=True)

        # Create database URL
        db_path = instance_dir / "aipackager.db"
        database_url = f"sqlite:///{db_path}"

        # Create service
        current_app.database_service = DatabaseService(database_url)
        current_app.database_service.create_tables()

    return current_app.database_service  # type: ignore[no-any-return]


def create_package(
    filename: str, file_path: str, custom_instructions: Optional[str] = None
) -> Package:
    """Create a new package record in the database.

    Args:
        filename: Original filename
        file_path: Path where file is stored
        custom_instructions: Optional custom instructions

    Returns:
        Created Package instance
    """
    db_service = get_database_service()

    session = db_service.get_session()
    try:
        package = Package(
            filename=filename,
            file_path=file_path,
            custom_instructions=custom_instructions,
        )
        session.add(package)
        session.commit()
        session.refresh(package)
        return package
    finally:
        session.close()


def get_package(package_id: str) -> Optional[Package]:
    """Get a package by ID.

    Args:
        package_id: UUID string of the package

    Returns:
        Package instance or None if not found
    """
    from uuid import UUID

    db_service = get_database_service()

    session = db_service.get_session()
    try:
        # Convert string to UUID for comparison
        try:
            uuid_obj = UUID(package_id)
        except ValueError:
            return None

        package = session.query(Package).filter(Package.id == uuid_obj).first()
        if package:
            # Ensure metadata is loaded
            _ = package.package_metadata
        return package  # type: ignore[no-any-return]
    finally:
        session.close()


def update_package_status(package_id: str, status: str) -> bool:
    """Update package status.

    Args:
        package_id: UUID string of the package
        status: New status

    Returns:
        True if updated successfully, False otherwise
    """
    from uuid import UUID

    db_service = get_database_service()

    session = db_service.get_session()
    try:
        try:
            uuid_obj = UUID(package_id)
        except ValueError:
            return False
        package = session.query(Package).filter(Package.id == uuid_obj).first()
        if package:
            package.status = status
            session.commit()
            return True
        return False
    finally:
        session.close()


def create_metadata(package_id: str, **metadata_fields: Any) -> Metadata:
    """Create metadata for a package.

    Args:
        package_id: UUID string of the package
        **metadata_fields: Metadata field values

    Returns:
        Created Metadata instance
    """
    db_service = get_database_service()

    session = db_service.get_session()
    try:
        metadata = Metadata(package_id=package_id, **metadata_fields)
        session.add(metadata)
        session.commit()
        session.refresh(metadata)
        return metadata
    finally:
        session.close()


def get_all_packages() -> list[Package]:
    """Get all packages from the database.

    Returns:
        List of Package instances
    """
    db_service = get_database_service()

    session = db_service.get_session()
    try:
        packages = session.query(Package).order_by(Package.upload_time.desc()).all()
        # Ensure metadata is loaded for all packages
        for package in packages:
            _ = package.package_metadata
        return packages  # type: ignore[no-any-return]
    finally:
        session.close()
