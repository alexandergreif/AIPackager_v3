# src/app/services/rag_service.py

"""
Stage 2+5: Targeted documentation queries
"""

from typing import List
from ..utils import retry_with_backoff
from .mcp_service import MCPService
from ..package_logger import get_package_logger


class RAGService:
    def __init__(self, package_id: str = "system"):
        self.package_logger = get_package_logger(package_id)
        self.mcp_service = MCPService(package_id)

    @retry_with_backoff()
    def query(self, cmdlets: List[str]) -> str:
        """
        Queries the RAG service for documentation on a list of cmdlets.
        Uses the crawl4ai-rag MCP server to get PSADT documentation.
        """
        query_text = " ".join(cmdlets)
        self.package_logger.log_step(
            "RAG_QUERY_START",
            f"Querying RAG for cmdlets: {query_text}",
            data={"source": "psappdeploytoolkit.com"},
        )
        response = self.mcp_service.perform_rag_query(
            query_text, source="psappdeploytoolkit.com"
        )
        self.package_logger.log_step(
            "RAG_QUERY_COMPLETE",
            "RAG query complete",
            data={"response": response},
        )
        return response
