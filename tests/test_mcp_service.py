# tests/test_mcp_service.py

import unittest
from unittest.mock import patch

from src.app.services.mcp_service import MCPService


class TestMCPService(unittest.TestCase):
    def setUp(self):
        self.mcp_service = MCPService(package_id="test_package")

    @patch("src.app.services.mcp_service.anyio.run")
    def test_perform_rag_query_success(self, mock_anyio_run):
        # Arrange
        mock_anyio_run.return_value = "Mock RAG response"
        query = "test query"
        source = "test_source"

        # Act
        response = self.mcp_service.perform_rag_query(query, source=source)

        # Assert
        mock_anyio_run.assert_called_once_with(
            self.mcp_service._call_mcp_tool_async,
            "crawl4ai-rag",
            "perform_rag_query",
            {"query": query, "source": source},
        )
        self.assertEqual(response, "Mock RAG response")

    @patch("src.app.services.mcp_service.anyio.run")
    def test_check_hallucinations_success(self, mock_anyio_run):
        # Arrange
        mock_anyio_run.return_value = {"status": "success", "issues": []}
        script_path = "/path/to/script.ps1"

        # Act
        response = self.mcp_service.check_hallucinations(script_path)

        # Assert
        mock_anyio_run.assert_called_once_with(
            self.mcp_service._call_mcp_tool_async,
            "crawl4ai-rag",
            "check_ai_script_hallucinations",
            {"script_path": script_path},
        )
        self.assertEqual(response, {"status": "success", "issues": []})

    @patch("src.app.services.mcp_service.anyio.run")
    def test_crawl_and_index_success(self, mock_anyio_run):
        # Arrange
        mock_anyio_run.return_value = {"status": "crawled"}
        url = "https://example.com"

        # Act
        response = self.mcp_service.crawl_and_index(url)

        # Assert
        mock_anyio_run.assert_called_once_with(
            self.mcp_service._call_mcp_tool_async,
            "crawl4ai-rag",
            "smart_crawl_url",
            {"url": url},
        )
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["response"], {"status": "crawled"})

    @patch("src.app.services.mcp_service.anyio.run")
    def test_perform_rag_query_failure(self, mock_anyio_run):
        # Arrange
        mock_anyio_run.side_effect = Exception("MCP server error")
        query = "test query"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.mcp_service.perform_rag_query(query)
        self.assertTrue("MCP server error" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
