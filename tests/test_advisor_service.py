import pytest
from unittest.mock import patch, MagicMock
from src.app.services.advisor_service import AdvisorService
from src.app.schemas import PSADTScript


@pytest.fixture
def advisor():
    return AdvisorService()


@patch("src.app.services.advisor_service.RAGService")
def test_advisor_service_no_correction_needed(mock_rag_service, advisor):
    """Test that the advisor service makes no changes when the script is clean."""
    # Arrange
    clean_script = PSADTScript(
        pre_installation_tasks=["Show-ADTInstallationWelcome"],
        installation_tasks=["Start-ADTMsiProcess -Action Install"],
    )
    hallucination_report = {"has_hallucinations": False, "issues": []}
    package_id = "test_package_clean"

    # Act
    corrected_script = advisor.correct_script(
        clean_script, hallucination_report, package_id
    )

    # Assert
    assert corrected_script == clean_script
    assert not corrected_script.corrections_applied
    mock_rag_service.assert_not_called()


@patch("src.app.services.advisor_service.OpenAI")
@patch("src.app.services.advisor_service.RAGService")
def test_advisor_service_corrects_unknown_cmdlet(
    mock_rag_service, mock_openai, advisor
):
    """Test that the advisor service uses RAG to correct an unknown cmdlet."""
    # Arrange
    script_with_hallucination = PSADTScript(
        installation_tasks=["Start-ADTMsiProcess -Action Install", "Fake-Command"],
    )
    hallucination_report = {
        "has_hallucinations": True,
        "issues": [{"type": "unknown_cmdlets", "cmdlets": ["Fake-Command"]}],
    }
    package_id = "test_package_correction"

    # Mock RAGService
    mock_rag_instance = mock_rag_service.return_value
    mock_rag_instance.query.return_value = "Documentation for Fake-Command"

    # Mock OpenAI response
    mock_openai_client = mock_openai.return_value
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[
        0
    ].message.content = (
        '{"installation_tasks": ["Start-ADTMsiProcess -Action Install"]}'
    )
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # Act
    corrected_script = advisor.correct_script(
        script_with_hallucination, hallucination_report, package_id
    )

    # Assert
    mock_rag_service.assert_called_once_with(package_id=package_id)
    mock_rag_instance.query.assert_called_once_with(["Fake-Command"])
    assert "Fake-Command" not in corrected_script.installation_tasks
    assert corrected_script.corrections_applied
    assert (
        "Corrected unknown cmdlets: Fake-Command"
        in corrected_script.corrections_applied
    )


@patch("src.app.services.advisor_service.RAGService")
def test_advisor_service_handles_empty_script(mock_rag_service, advisor):
    """Test that the advisor service handles an empty script gracefully."""
    # Arrange
    empty_script = PSADTScript()
    hallucination_report = {"has_hallucinations": False, "issues": []}
    package_id = "test_package_empty"

    # Act
    corrected_script = advisor.correct_script(
        empty_script, hallucination_report, package_id
    )

    # Assert
    assert corrected_script == empty_script
    assert not corrected_script.corrections_applied
    mock_rag_service.assert_not_called()
