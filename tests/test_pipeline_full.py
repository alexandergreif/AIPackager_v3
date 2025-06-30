import time
from io import BytesIO
import pytest
from unittest.mock import patch
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


@patch("src.app.services.mcp_service.use_mcp_tool")
def test_full_pipeline_with_mocked_mcp(mock_use_mcp_tool, app_with_db):
    """Test the full pipeline with mocked MCP interactions."""
    client = app_with_db.test_client()

    # Configure mock responses for MCP tools
    def mcp_tool_router(*args, **kwargs):
        if kwargs.get("tool_name") == "perform_rag_query":
            return "Mocked RAG documentation"
        if kwargs.get("tool_name") == "check_ai_script_hallucinations":
            return {"status": "success", "issues": []}
        return {}

    mock_use_mcp_tool.side_effect = mcp_tool_router

    # 1. Upload a dummy installer
    data = {
        "installer": (BytesIO(b"dummy content"), "dummy.msi"),
        "custom_instructions": "Install this application silently.",
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

        # Verify MCP calls
        rag_call_args = [
            c
            for c in mock_use_mcp_tool.call_args_list
            if c[1]["tool_name"] == "perform_rag_query"
        ]
        hallucination_call_args = [
            c
            for c in mock_use_mcp_tool.call_args_list
            if c[1]["tool_name"] == "check_ai_script_hallucinations"
        ]

        assert len(rag_call_args) > 0
        assert rag_call_args[0][1]["source"] == "psappdeploytoolkit.com"
        assert len(hallucination_call_args) == 1

        # Check hallucination report
        assert package.hallucination_report is not None
        assert package.hallucination_report["status"] == "success"
