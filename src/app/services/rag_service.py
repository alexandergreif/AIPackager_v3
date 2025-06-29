# src/app/services/rag_service.py

"""
Stage 2+5: Targeted documentation queries
"""

from typing import List
from ..utils import retry_with_backoff
from .mcp_service import mcp_service


class RAGService:
    @retry_with_backoff()
    def query(self, cmdlets: List[str]) -> str:
        """
        Queries the RAG service for documentation on a list of cmdlets.
        Uses the crawl4ai-rag MCP server to get PSADT documentation.
        """
        query_text = " ".join(cmdlets)
        return mcp_service.perform_rag_query(query_text)
