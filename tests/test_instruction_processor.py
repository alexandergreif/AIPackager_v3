from src.app.services.instruction_processor import InstructionProcessor
from src.app.schemas import InstructionResult


def test_instruction_processor_simple_instruction():
    """Test that a simple instruction is processed correctly."""
    processor = InstructionProcessor()
    result = processor.process_instructions("Install the application")
    assert isinstance(result, InstructionResult)
    assert "Install-MSI" in result.predicted_cmdlets
    assert result.confidence_score > 0.5


def test_instruction_processor_with_custom_steps():
    """Test that custom steps are correctly identified."""
    processor = InstructionProcessor()
    result = processor.process_instructions(
        "Install the application and then run a custom script."
    )
    assert isinstance(result, InstructionResult)
    assert "Install-MSI" in result.predicted_cmdlets
    assert "Execute-Process" in result.predicted_cmdlets
    assert result.confidence_score > 0.5


def test_instruction_processor_with_no_clear_action():
    """Test that a vague instruction returns a low confidence score."""
    processor = InstructionProcessor()
    result = processor.process_instructions("I want to package this application.")
    assert isinstance(result, InstructionResult)
    assert result.confidence_score < 0.5
