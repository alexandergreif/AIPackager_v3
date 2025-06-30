# tests/test_rag_service.py

import unittest
from unittest.mock import patch

from src.app.services.rag_service import RAGService


class TestRAGService(unittest.TestCase):
    def setUp(self):
        self.rag_service = RAGService(package_id="test_package")

    @patch("src.app.services.rag_service.mcp_service")
    def test_query_success(self, mock_mcp_service):
        # Arrange
        mock_mcp_service.perform_rag_query.return_value = "Mock documentation"
        cmdlets = ["Get-Process", "Get-Service"]
        expected_query = "Get-Process Get-Service"
        expected_source = "psappdeploytoolkit.com"

        # Act
        response = self.rag_service.query(cmdlets)

        # Assert
        mock_mcp_service.perform_rag_query.assert_called_once_with(
            expected_query, source=expected_source
        )
        self.assertEqual(response, "Mock documentation")

    @patch("src.app.services.rag_service.mcp_service")
    def test_query_empty_list(self, mock_mcp_service):
        # Arrange
        mock_mcp_service.perform_rag_query.return_value = "Empty response"
        cmdlets = []
        expected_query = ""
        expected_source = "psappdeploytoolkit.com"

        # Act
        response = self.rag_service.query(cmdlets)

        # Assert
        mock_mcp_service.perform_rag_query.assert_called_once_with(
            expected_query, source=expected_source
        )
        self.assertEqual(response, "Empty response")


if __name__ == "__main__":
    unittest.main()
