import time
from io import BytesIO
from unittest.mock import patch

import pytest

from src.app import create_app
from src.app.database import get_database_service
from src.app.models import Package
from src.app.schemas import InstructionResult
import uuid


def wait_for_completion(client, pkg_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        resp = client.get(
            f"/progress/{pkg_id}", headers={"X-Requested-With": "XMLHttpRequest"}
        )
        if resp.status_code != 200:
            time.sleep(0.1)
            continue
        data = resp.get_json()
        if data["progress"] == 100:
            return True
        time.sleep(0.1)
    return False


@pytest.fixture
def app_with_db(tmp_path):
    app = create_app({"TESTING": True})
    app.instance_path = str(tmp_path)
    with app.app_context():
        db_service = get_database_service()
        db_service.create_tables()
    yield app


def test_full_pipeline_flow(app_with_db):
    client = app_with_db.test_client()

    mocks = {
        "instruction": patch(
            "src.app.services.script_generator.InstructionProcessor"
        ),
        "advisor": patch(
            "src.app.services.script_generator.AdvisorService"
        ),
        "rag": patch(
            "src.app.services.script_generator.RAGService.query",
            return_value="docs",
        ),
        "detect": patch(
            "src.app.services.script_generator.HallucinationDetector.detect",
            return_value={"has_hallucinations": False},
        ),
    }

    with (
        mocks["instruction"] as MockInstr,
        mocks["advisor"],
        mocks["rag"],
        mocks["detect"],
    ):
        MockInstr.return_value.process_instructions.return_value = InstructionResult(
            structured_instructions={"user_instructions": "Install"},
            predicted_cmdlets=["Start-ADTMsiProcess"],
            confidence_score=0.9,
        )
        data = {"installer": (BytesIO(b"abc"), "dummy.msi")}
        resp = client.post("/api/packages", data=data)
        pkg_id = resp.get_json()["package_id"]

        resp = client.post(f"/api/packages/{pkg_id}/generate")
        assert resp.status_code == 202

        assert wait_for_completion(client, pkg_id)

        with app_with_db.app_context():
            db_service = get_database_service()
            session = db_service.get_session()
            try:
                pkg = session.get(Package, uuid.UUID(pkg_id))
                assert pkg is not None
                assert pkg.generated_script is not None
            finally:
                session.close()
