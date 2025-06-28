import json
from unittest.mock import MagicMock, patch

from src.app.services.instruction_processor import InstructionProcessor


def test_process_instructions_extracts_predicted_processes():
    response_json = json.dumps(
        {
            "structured_instructions": {"primary_action": "install"},
            "predicted_cmdlets": ["Start-ADTMsiProcess"],
            "predicted_processes_to_close": ["chrome.exe", "teams.exe"],
            "confidence_score": 0.95,
        }
    )

    mock_message = MagicMock()
    mock_message.content = response_json
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])

    mock_client = MagicMock()
    mock_client.api_key = "dummy"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.app.services.instruction_processor.OpenAI", return_value=mock_client):
        processor = InstructionProcessor()
        result = processor.process_instructions("Install")

    assert result.predicted_processes_to_close == ["chrome.exe", "teams.exe"]
    assert result.predicted_cmdlets == ["Start-ADTMsiProcess"]
