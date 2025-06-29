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


def test_psadt_generator_happy_path():
    """Test the full PSADT generator pipeline with a simple, clean instruction."""
    generator = PSADTGenerator()
    result = generator.generate_script("Install the application silently.")

    assert isinstance(result, PSADTScript)
    assert result.hallucination_report is not None
    assert not result.hallucination_report["has_hallucinations"]
    assert "Start-ADTMsiProcess" in result.installation_tasks[0]


def test_psadt_generator_with_hallucinations():
    """Test the full PSADT generator pipeline with a hallucinated instruction."""
    generator = PSADTGenerator()
    result = generator.generate_script("Install the application with Fake-Command.")

    assert isinstance(result, PSADTScript)
    assert result.hallucination_report is not None
    assert result.hallucination_report["has_hallucinations"]
    assert result.corrections_applied is not None
    assert "Fake-Command" not in result.installation_tasks
    assert "Removed unknown cmdlet: Fake-Command" in result.corrections_applied[0]


def test_hallucination_detector_more_cases():
    """Test hallucination detection functionality with more cases."""
    from src.app.services.hallucination_detector import HallucinationDetector

    detector = HallucinationDetector()

    # Test with mixed known and unknown cmdlets
    mixed_script = """
    Show-ADTInstallationWelcome
    Fake-Command -Parameter Value
    Start-ADTMsiProcess -Action Install
    Another-Fake-Command
    """
    result = detector.detect(mixed_script)
    assert result["has_hallucinations"]
    assert len(result["issues"]) == 1
    assert "Fake-Command" in result["issues"][0]["cmdlets"]
    assert "Another-Fake-Command" in result["issues"][0]["cmdlets"]

    # Test with no cmdlets
    no_cmdlet_script = "Write-Host 'Hello, World!'"
    result = detector.detect(no_cmdlet_script)
    assert not result["has_hallucinations"]
    assert result["confidence_score"] == 1.0


def test_rag_service_edge_cases():
    """Test RAG service functionality with edge cases."""
    from src.app.services.rag_service import RAGService

    rag = RAGService()

    # Test with an empty list of cmdlets
    result = rag.query([])
    assert result == ""

    # Test with a mix of known and unknown cmdlets
    result = rag.query(["Show-ADTInstallationWelcome", "Unknown-Cmdlet"])
    assert "Show-ADTInstallationWelcome" in result
    assert "Unknown-Cmdlet" in result
