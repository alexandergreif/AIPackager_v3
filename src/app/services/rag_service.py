# src/app/services/rag_service.py

"""
Stage 2+5: Targeted documentation queries
"""

from typing import List
from ..utils import retry_with_backoff


class RAGService:
    @retry_with_backoff()
    def query(self, cmdlets: List[str]) -> str:
        """
        Queries the RAG service for documentation on a list of cmdlets.
        Uses the crawl4ai-rag MCP server to get PSADT documentation.
        """
        # For now, we'll use a mock implementation that simulates RAG queries
        # In a real implementation, this would use the MCP tools
        query_text = " ".join(cmdlets)

        # Mock response based on common PSADT cmdlets
        mock_docs = {
            "Show-ADTInstallationWelcome": "Displays a welcome dialog to the user before installation begins.",
            "Start-ADTMsiProcess": "Executes an MSI installer with specified parameters and logging.",
            "Show-ADTInstallationProgress": "Shows a progress dialog during installation operations.",
            "Show-ADTInstallationPrompt": "Displays a prompt dialog for user interaction.",
            "Remove-ADTFile": "Removes files or directories with proper error handling.",
            "Copy-ADTFile": "Copies files with verification and logging.",
            "Set-ADTRegistryKey": "Creates or modifies registry keys and values.",
            "Get-ADTRegistryKey": "Retrieves registry key values with error handling.",
        }

        # Return documentation for matching cmdlets
        relevant_docs = []
        for cmdlet in cmdlets:
            if cmdlet in mock_docs:
                relevant_docs.append(f"{cmdlet}: {mock_docs[cmdlet]}")

        if relevant_docs:
            return "\n".join(relevant_docs)
        else:
            return f"Documentation for PSADT cmdlets: {query_text}"
