# src/app/services/mcp_service.py

"""
Service for interacting with the Model Context Protocol (MCP) server.
"""

import anyio
from typing import Any, Optional, cast

from ..package_logger import get_package_logger
from ..utils import retry_with_backoff
from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPService:
    def __init__(self, package_id: str = "system"):
        self.package_logger = get_package_logger(package_id)

    async def _call_mcp_tool_async(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Helper to call an MCP tool asynchronously."""
        # The server_name parameter is kept for potential future use,
        # but for now, we connect to a hardcoded URL.
        url = (
            "http://127.0.0.1:8052/sse"  # Correct SSE endpoint from Cline configuration
        )

        self.package_logger.log_step(
            "MCP_CONNECTION_ATTEMPT",
            f"Attempting MCP connection to {url} for tool {tool_name}",
            data={"url": url, "tool_name": tool_name, "arguments": arguments},
        )

        try:
            async with sse_client(url) as (read, write):
                self.package_logger.log_step(
                    "MCP_TRANSPORT_CONNECTED",
                    "MCP transport connected successfully",
                )

                async with ClientSession(read, write) as session:
                    self.package_logger.log_step(
                        "MCP_SESSION_CREATED",
                        "MCP session created, attempting initialization",
                    )

                    await session.initialize()

                    self.package_logger.log_step(
                        "MCP_SESSION_INITIALIZED",
                        "MCP session initialized successfully",
                    )

                    result = await session.call_tool(tool_name, arguments)

                    if result.isError:
                        error_message = (
                            f"MCP tool call failed for {tool_name}: {result.content}"
                        )
                        self.package_logger.log_step(
                            "MCP_TOOL_ERROR",
                            error_message,
                            data={
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "error_content": result.content,
                            },
                        )
                        raise Exception(error_message)

                    # Parse the response properly - MCP returns TextContent objects
                    response_data: dict[str, Any] | list[Any] | str = (
                        result.structuredContent or result.content
                    )

                    # If it's a list of TextContent objects, extract the text
                    if isinstance(response_data, list) and response_data:
                        # Get the first TextContent object and extract its text
                        text_content = (
                            response_data[0].text
                            if hasattr(response_data[0], "text")
                            else str(response_data[0])
                        )
                        try:
                            # Try to parse as JSON if it looks like JSON
                            import json

                            if text_content.strip().startswith("{"):
                                response_data = json.loads(text_content)
                            else:
                                response_data = text_content
                        except (json.JSONDecodeError, AttributeError):
                            response_data = text_content

                    self.package_logger.log_step(
                        "MCP_TOOL_SUCCESS",
                        f"MCP tool call successful for {tool_name}",
                        data={
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "response": response_data,
                        },
                    )
                    return response_data

        except Exception as e:
            self.package_logger.log_step(
                "MCP_CONNECTION_ERROR",
                f"MCP connection failed: {str(e)}",
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "url": url,
                    "tool_name": tool_name,
                },
            )
            raise

    @retry_with_backoff()
    def crawl_and_index(self, url: str) -> dict:
        """
        Uses the crawl4ai-rag MCP server to crawl and index a URL.
        """
        self.package_logger.log_step(
            "MCP_CRAWL_START", f"Starting crawl and index for URL: {url}"
        )
        try:
            response = anyio.run(
                self._call_mcp_tool_async,
                "crawl4ai-rag",
                "smart_crawl_url",
                {"url": url},
            )
            self.package_logger.log_step(
                "MCP_CRAWL_COMPLETE",
                f"Crawl and index complete for URL: {url}",
                data={"response": response},
            )
            return {
                "status": "success",
                "message": f"Crawled and indexed {url}",
                "response": response,
            }
        except Exception as e:
            self.package_logger.log_step(
                "MCP_CRAWL_FAILED",
                f"Crawl and index failed for URL: {url}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    def perform_rag_query(self, query: str, source: Optional[str] = None) -> str:
        """
        Performs a RAG query using the crawl4ai-rag MCP server.
        """
        self.package_logger.log_step(
            "MCP_RAG_QUERY_START", f"Performing RAG query: {query}, Source: {source}"
        )
        try:
            response = anyio.run(
                self._call_mcp_tool_async,
                "crawl4ai-rag",
                "perform_rag_query",
                {"query": query, "source": source},
            )
            self.package_logger.log_step(
                "MCP_RAG_QUERY_COMPLETE",
                "RAG query complete",
                data={"response": response},
            )
            return cast(str, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_RAG_QUERY_FAILED",
                f"RAG query failed for query: {query}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    def check_hallucinations(self, script_path: str) -> dict:
        """
        Checks an AI-generated Python script for hallucinations using the knowledge graph.
        """
        self.package_logger.log_step(
            "MCP_HALLUCINATION_CHECK_START",
            f"Starting hallucination check for script: {script_path}",
        )
        try:
            response = anyio.run(
                self._call_mcp_tool_async,
                "crawl4ai-rag",
                "check_ai_script_hallucinations",
                {"script_path": script_path},
            )
            self.package_logger.log_step(
                "MCP_HALLUCINATION_CHECK_COMPLETE",
                "Hallucination check complete",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_HALLUCINATION_CHECK_FAILED",
                f"Hallucination check failed for script: {script_path}",
                data={"error": str(e)},
            )
            raise


mcp_service = MCPService()
