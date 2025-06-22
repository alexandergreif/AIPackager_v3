"""Tests for SQLAlchemy models."""

import pytest
from datetime import datetime
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.models import Base, Package, Metadata


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestPackageModel:
    """Test Package model functionality."""

    def test_package_creation(self, session):
        """Test creating a Package instance."""
        package = Package(
            filename="test.msi",
            file_path="/uploads/uuid_test.msi",
            custom_instructions="Test instructions",
        )

        session.add(package)
        session.commit()

        # Verify package was created with UUID
        assert isinstance(package.id, UUID)
        assert package.filename == "test.msi"
        assert package.file_path == "/uploads/uuid_test.msi"
        assert package.status == "uploading"  # Default status
        assert package.custom_instructions == "Test instructions"
        assert isinstance(package.upload_time, datetime)

    def test_package_status_enum(self, session):
        """Test Package status enum values."""
        valid_statuses = ["uploading", "processing", "completed", "failed"]

        for status in valid_statuses:
            package = Package(
                filename=f"test_{status}.msi",
                file_path=f"/uploads/{status}.msi",
                status=status,
            )
            session.add(package)
            session.commit()
            assert package.status == status

    def test_package_repr(self, session):
        """Test Package string representation."""
        package = Package(filename="test.msi", file_path="/uploads/test.msi")
        session.add(package)
        session.commit()

        repr_str = repr(package)
        assert "Package" in repr_str
        assert "test.msi" in repr_str
        assert str(package.id) in repr_str


class TestMetadataModel:
    """Test Metadata model functionality."""

    def test_metadata_creation(self, session):
        """Test creating a Metadata instance linked to Package."""
        # Create package first
        package = Package(filename="test.msi", file_path="/uploads/test.msi")
        session.add(package)
        session.commit()

        # Create metadata
        metadata = Metadata(
            package_id=package.id,
            product_name="Test Product",
            version="1.0.0",
            publisher="Test Publisher",
            install_date="2025-01-01",
            uninstall_string="msiexec /x {GUID}",
            estimated_size=1024,
        )

        session.add(metadata)
        session.commit()

        # Verify metadata was created
        assert isinstance(metadata.id, UUID)
        assert metadata.package_id == package.id
        assert metadata.product_name == "Test Product"
        assert metadata.version == "1.0.0"
        assert metadata.publisher == "Test Publisher"
        assert metadata.install_date == "2025-01-01"
        assert metadata.uninstall_string == "msiexec /x {GUID}"
        assert metadata.estimated_size == 1024

    def test_package_metadata_relationship(self, session):
        """Test relationship between Package and Metadata."""
        # Create package
        package = Package(filename="test.msi", file_path="/uploads/test.msi")
        session.add(package)
        session.commit()

        # Create metadata
        metadata = Metadata(
            package_id=package.id, product_name="Test Product", version="1.0.0"
        )
        session.add(metadata)
        session.commit()

        # Test relationship access
        assert package.package_metadata is not None
        assert package.package_metadata.product_name == "Test Product"
        assert metadata.package == package
        assert metadata.package.filename == "test.msi"

    def test_metadata_repr(self, session):
        """Test Metadata string representation."""
        package = Package(filename="test.msi", file_path="/uploads/test.msi")
        session.add(package)
        session.commit()

        metadata = Metadata(
            package_id=package.id, product_name="Test Product", version="1.0.0"
        )
        session.add(metadata)
        session.commit()

        repr_str = repr(metadata)
        assert "Metadata" in repr_str
        assert "Test Product" in repr_str
        assert "1.0.0" in repr_str


class TestModelConstraints:
    """Test model constraints and validations."""

    def test_package_required_fields(self, session):
        """Test that required fields are enforced."""
        # Should fail without filename
        with pytest.raises(Exception):
            package = Package(file_path="/uploads/test.msi")
            session.add(package)
            session.commit()

    def test_metadata_foreign_key_constraint(self, session):
        """Test foreign key constraint on metadata."""
        # Test that metadata can be created with valid package_id
        package = Package(filename="test.msi", file_path="/uploads/test.msi")
        session.add(package)
        session.commit()

        # This should work fine
        metadata = Metadata(package_id=package.id, product_name="Test Product")
        session.add(metadata)
        session.commit()

        assert metadata.package_id == package.id
        assert metadata.product_name == "Test Product"
