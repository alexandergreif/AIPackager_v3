from unittest.mock import patch

from src.app import create_app
from src.app.database import get_database_service, create_package, get_package


def test_generate_script_async_failure_marks_failed(tmp_path):
    app = create_app({"DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"})
    app.instance_path = str(tmp_path)

    with app.app_context():
        db_service = get_database_service()
        db_service.create_tables()
        pkg = create_package("test.msi", str(tmp_path / "test.msi"))
        pkg_id = str(pkg.id)

    client = app.test_client()

    with patch("requests.post", side_effect=Exception("boom")):
        with patch("threading.Thread.start", lambda self: self.run()):
            client.get(f"/progress/{pkg_id}")

    with app.app_context():
        refreshed = get_package(pkg_id)
        assert refreshed is not None
        assert refreshed.status == "failed"
