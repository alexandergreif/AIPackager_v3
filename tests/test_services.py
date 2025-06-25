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

    result = generator.generate_script("test instructions")

    assert isinstance(result, PSADTScript)
    mock_services["instruction_processor"].process_instructions.assert_called_once_with(
        "test instructions"
    )
