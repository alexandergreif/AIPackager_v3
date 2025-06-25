# tests/test_services.py
import pytest
from unittest.mock import patch
from src.app.services.script_generator import PSADTGenerator
from src.app.schemas import InstructionResult, PSADTScript


@pytest.fixture
def mock_services():
    with (
        patch(
            "src.app.services.script_generator.InstructionProcessor"
        ) as MockInstructionProcessor,
        patch("src.app.services.script_generator.RAGService") as MockRAGService,
        patch(
            "src.app.services.script_generator.HallucinationDetector"
        ) as MockHallucinationDetector,
        patch("src.app.services.script_generator.AdvisorService") as MockAdvisorService,
    ):
        mock_instruction_processor = MockInstructionProcessor.return_value
        mock_instruction_processor.process_instructions.return_value = (
            InstructionResult(
                structured_instructions={"install": "test"},
                predicted_cmdlets=["Install-MSI"],
                confidence_score=0.9,
            )
        )

        yield {
            "instruction_processor": mock_instruction_processor,
            "rag_service": MockRAGService.return_value,
            "hallucination_detector": MockHallucinationDetector.return_value,
            "advisor_service": MockAdvisorService.return_value,
        }


def test_psadt_generator_happy_path(mock_services):
    generator = PSADTGenerator()

    # Override the mocked services in the generator instance
    generator.instruction_processor = mock_services["instruction_processor"]
    generator.rag_service = mock_services["rag_service"]
    generator.hallucination_detector = mock_services["hallucination_detector"]
    generator.advisor_service = mock_services["advisor_service"]

    # Mock RAG and hallucination detection responses
    mock_services["rag_service"].query.return_value = "Mock PSADT documentation"
    mock_services["hallucination_detector"].detect.return_value = {
        "has_hallucinations": False,
        "confidence_score": 0.95,
        "issues": [],
    }

    result = generator.generate_script("test instructions")

    assert isinstance(result, PSADTScript)
    assert result.hallucination_report is not None
    assert not result.hallucination_report["has_hallucinations"]

    # Verify all stages were called
    mock_services["instruction_processor"].process_instructions.assert_called_once_with(
        "test instructions"
    )
    mock_services["rag_service"].query.assert_called_once()
    mock_services["hallucination_detector"].detect.assert_called_once()
    # Advisor should not be called when no hallucinations detected
    mock_services["advisor_service"].correct_script.assert_not_called()


def test_psadt_generator_with_hallucinations(mock_services):
    """Test 5-stage pipeline when hallucinations are detected."""
    generator = PSADTGenerator()

    # Override the mocked services in the generator instance
    generator.instruction_processor = mock_services["instruction_processor"]
    generator.rag_service = mock_services["rag_service"]
    generator.hallucination_detector = mock_services["hallucination_detector"]
    generator.advisor_service = mock_services["advisor_service"]

    # Mock responses with hallucinations detected
    mock_services["rag_service"].query.return_value = "Mock PSADT documentation"
    mock_services["hallucination_detector"].detect.return_value = {
        "has_hallucinations": True,
        "confidence_score": 0.6,
        "issues": [{"type": "unknown_cmdlets", "cmdlets": ["Fake-ADTCmdlet"]}],
    }

    # Mock corrected script
    corrected_script = PSADTScript(
        pre_installation_tasks=["Show-ADTInstallationWelcome"],
        installation_tasks=["Start-ADTMsiProcess -Action Install"],
        post_installation_tasks=["Show-ADTInstallationProgress"],
        uninstallation_tasks=["Start-ADTMsiProcess -Action Uninstall"],
        post_uninstallation_tasks=["Remove-ADTRegistryKey"],
        corrections_applied=["Removed unknown cmdlet: Fake-ADTCmdlet"],
    )
    mock_services["advisor_service"].correct_script.return_value = corrected_script

    result = generator.generate_script("test instructions")

    assert isinstance(result, PSADTScript)
    assert result.hallucination_report is not None
    assert result.hallucination_report["has_hallucinations"]
    assert result.corrections_applied is not None

    # Verify advisor was called for correction
    mock_services["advisor_service"].correct_script.assert_called_once()


def test_hallucination_detector():
    """Test hallucination detection functionality."""
    from src.app.services.hallucination_detector import HallucinationDetector

    detector = HallucinationDetector()

    # Test script with known cmdlets (should pass)
    clean_script = """
    Show-ADTInstallationWelcome -CloseAppsCountdown 60
    Start-ADTMsiProcess -Action Install -Path '$dirFiles\\setup.msi'
    """

    result = detector.detect(clean_script)
    assert not result["has_hallucinations"]
    assert result["confidence_score"] > 0.9

    # Test script with unknown cmdlets (should fail)
    bad_script = """
    Show-ADTInstallationWelcome -CloseAppsCountdown 60
    Show-ADTFakeCmdlet -Parameter Value
    Start-ADTMsiProcess -Action Install -Path '$dirFiles\\setup.msi'
    """

    result = detector.detect(bad_script)
    assert result["has_hallucinations"]
    assert result["confidence_score"] < 0.8
    assert len(result["issues"]) > 0


def test_rag_service():
    """Test RAG service functionality."""
    from src.app.services.rag_service import RAGService

    rag = RAGService()

    # Test with known cmdlets
    result = rag.query(["Show-ADTInstallationWelcome", "Start-ADTMsiProcess"])
    assert isinstance(result, str)
    assert "Show-ADTInstallationWelcome" in result
    assert "Start-ADTMsiProcess" in result

    # Test with unknown cmdlets
    result = rag.query(["Unknown-Cmdlet"])
    assert isinstance(result, str)
    assert "Unknown-Cmdlet" in result
