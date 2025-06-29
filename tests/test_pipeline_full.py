import time
from io import BytesIO
import pytest
from src.app import create_app
from src.app.database import get_database_service, get_package


def wait_for_completion(client, pkg_id, timeout=30):
    """Wait for the pipeline to complete."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        response = client.get(f"/api/packages/{pkg_id}")
        if response.status_code == 200:
            data = response.get_json()
            if data.get("status") == "completed":
                return True
        time.sleep(1)
    return False


@pytest.fixture
def app_with_db(tmp_path):
    """Create a test app with a temporary database."""
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path}/test.db"})
    with app.app_context():
        db_service = get_database_service()
        db_service.create_tables()
    yield app


def test_full_pipeline_e2e(app_with_db):
    """Test the full end-to-end pipeline without mocks."""
    client = app_with_db.test_client()

    # 1. Upload a dummy installer
    data = {
        "installer": (BytesIO(b"dummy content"), "dummy.msi"),
        "custom_instructions": "Install this application silently and then remove the desktop shortcut.",
    }
    response = client.post("/api/packages", data=data)
    assert response.status_code == 200
    package_id = response.get_json()["package_id"]

    # 2. Trigger the generation pipeline
    response = client.post(f"/api/packages/{package_id}/generate")
    assert response.status_code == 202

    # 3. Wait for completion
    assert wait_for_completion(client, package_id), "Pipeline did not complete in time."

    # 4. Verify the results
    with app_with_db.app_context():
        package = get_package(package_id)
        assert package is not None
        assert package.status == "completed"
        assert package.generated_script is not None

        # Check for expected commands in the generated script
        install_tasks = package.generated_script.get("installation_tasks", [])
        post_install_tasks = package.generated_script.get("post_installation_tasks", [])

        assert any("Start-ADTMsiProcess" in task for task in install_tasks)
        assert any("Remove-File" in task for task in post_install_tasks)

        # Check hallucination report
        assert package.hallucination_report is not None
        assert not package.hallucination_report["has_hallucinations"]
