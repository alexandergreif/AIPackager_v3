"""Tests for the job resume functionality."""

from src.app import create_app
from src.app.database import get_database_service, get_package, Package


def test_resume_pending_jobs(tmp_path):
    """Test that pending jobs are resumed on app start."""
    db_path = tmp_path / "test.db"
    app = create_app({"DATABASE_URL": f"sqlite:///{db_path}"})

    with app.app_context():
        db_service = get_database_service()
        db_service.create_tables()

        # Create a package with a status of "processing"
        package = Package(
            filename="test.msi",
            file_path="/path/to/test.msi",
            status="processing",
        )
        db_service.get_session().add(package)
        db_service.get_session().commit()
        package_id = package.id

    # Restart the app
    app = create_app({"DATABASE_URL": f"sqlite:///{db_path}"})

    with app.app_context():
        # The resume logic should have run on app start
        retrieved_package = get_package(package_id)
        assert retrieved_package.status == "completed"
