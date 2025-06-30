# tests/test_hallucination_detector.py

import unittest
from unittest.mock import patch

from src.app.services.hallucination_detector_service import HallucinationDetectorService


class TestHallucinationDetectorService(unittest.TestCase):
    def setUp(self):
        self.detector_service = HallucinationDetectorService(package_id="test_package")

    @patch("src.app.services.hallucination_detector_service.mcp_service")
    def test_detect_hallucinations_success(self, mock_mcp_service):
        # Arrange
        mock_mcp_service.check_hallucinations.return_value = {
            "status": "success",
            "issues": [],
        }
        script_path = "/path/to/script.ps1"

        # Act
        report = self.detector_service.detect_hallucinations(script_path)

        # Assert
        mock_mcp_service.check_hallucinations.assert_called_once_with(script_path)
        self.assertEqual(report, {"status": "success", "issues": []})

    @patch("src.app.services.hallucination_detector_service.mcp_service")
    def test_detect_hallucinations_failure(self, mock_mcp_service):
        # Arrange
        mock_mcp_service.check_hallucinations.side_effect = Exception("MCP error")
        script_path = "/path/to/script.ps1"

        # Act
        report = self.detector_service.detect_hallucinations(script_path)

        # Assert
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["issues"][0]["type"], "detection_failed")
        self.assertEqual(report["issues"][0]["message"], "MCP error")


if __name__ == "__main__":
    unittest.main()
