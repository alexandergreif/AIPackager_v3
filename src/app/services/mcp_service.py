# src/app/services/mcp_service.py

"""
Service for interacting with the Model Context Protocol (MCP) server.
"""

from typing import Any, Optional, cast, Dict

from ..package_logger import get_package_logger
from ..utils import retry_with_backoff
from ..config import MCPConfigLoader
from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPService:
    def __init__(self, package_id: str = "system"):
        self.package_logger = get_package_logger(package_id)
        try:
            self.config_loader: Optional[MCPConfigLoader] = MCPConfigLoader()
            self.server_config = self.config_loader.get_server_config("crawl4ai-rag")
        except Exception as e:
            self.package_logger.log_step(
                "MCP_CONFIG_ERROR",
                f"Failed to load MCP configuration: {str(e)}",
                data={"error": str(e), "error_type": type(e).__name__},
            )
            # Fallback to empty config
            self.config_loader = None
            self.server_config = {}

    async def _call_mcp_tool_async(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Helper to call an MCP tool asynchronously."""
        # Get URL from configuration or use fallback
        if self.config_loader and self.server_config:
            try:
                url = self.config_loader.get_server_url(server_name)
            except KeyError:
                url = "http://127.0.0.1:8052/sse"  # Fallback URL
        else:
            url = "http://127.0.0.1:8052/sse"  # Fallback URL

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
    async def crawl_and_index(self, url: str) -> dict:
        """
        Uses the crawl4ai-rag MCP server to crawl and index a URL.
        """
        self.package_logger.log_step(
            "MCP_CRAWL_START", f"Starting crawl and index for URL: {url}"
        )
        try:
            response = await self._call_mcp_tool_async(
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
    async def perform_rag_query(self, query: str, source: Optional[str] = None) -> str:
        """
        Performs a RAG query using the crawl4ai-rag MCP server.
        """
        self.package_logger.log_step(
            "MCP_RAG_QUERY_START", f"Performing RAG query: {query}, Source: {source}"
        )
        try:
            response = await self._call_mcp_tool_async(
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
    async def check_hallucinations(self, script_path: str) -> dict:
        """
        Checks an AI-generated Python script for hallucinations using the knowledge graph.
        """
        self.package_logger.log_step(
            "MCP_HALLUCINATION_CHECK_START",
            f"Starting hallucination check for script: {script_path}",
        )
        try:
            response = await self._call_mcp_tool_async(
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

    # New methods for Tools page functionality

    @retry_with_backoff()
    async def get_available_sources(self) -> dict:
        """Get all available sources from the knowledge base."""
        self.package_logger.log_step(
            "MCP_GET_SOURCES_START", "Getting available knowledge base sources"
        )
        try:
            response = await self._call_mcp_tool_async(
                "crawl4ai-rag",
                "get_available_sources",
                {},
            )
            self.package_logger.log_step(
                "MCP_GET_SOURCES_COMPLETE",
                "Successfully retrieved available sources",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_GET_SOURCES_FAILED",
                f"Failed to get available sources: {str(e)}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    async def crawl_single_page(self, url: str) -> dict:
        """Crawl a single page and add to knowledge base."""
        self.package_logger.log_step(
            "MCP_CRAWL_SINGLE_START", f"Starting single page crawl for URL: {url}"
        )
        try:
            response = await self._call_mcp_tool_async(
                "crawl4ai-rag",
                "crawl_single_page",
                {"url": url},
            )
            self.package_logger.log_step(
                "MCP_CRAWL_SINGLE_COMPLETE",
                f"Single page crawl complete for URL: {url}",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_CRAWL_SINGLE_FAILED",
                f"Single page crawl failed for URL: {url}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    async def smart_crawl_url(
        self,
        url: str,
        max_depth: int = 3,
        max_concurrent: int = 10,
        chunk_size: int = 5000,
    ) -> dict:
        """Smart crawl a URL with advanced options."""
        self.package_logger.log_step(
            "MCP_SMART_CRAWL_START",
            f"Starting smart crawl for URL: {url}",
            data={
                "url": url,
                "max_depth": max_depth,
                "max_concurrent": max_concurrent,
                "chunk_size": chunk_size,
            },
        )
        try:
            response = await self._call_mcp_tool_async(
                "crawl4ai-rag",
                "smart_crawl_url",
                {
                    "url": url,
                    "max_depth": max_depth,
                    "max_concurrent": max_concurrent,
                    "chunk_size": chunk_size,
                },
            )
            self.package_logger.log_step(
                "MCP_SMART_CRAWL_COMPLETE",
                f"Smart crawl complete for URL: {url}",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_SMART_CRAWL_FAILED",
                f"Smart crawl failed for URL: {url}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    async def parse_github_repository(self, repo_url: str) -> dict:
        """Parse a GitHub repository into the knowledge graph."""
        self.package_logger.log_step(
            "MCP_PARSE_REPO_START",
            f"Starting GitHub repository parse for URL: {repo_url}",
        )
        try:
            response = await self._call_mcp_tool_async(
                "crawl4ai-rag",
                "parse_github_repository",
                {"repo_url": repo_url},
            )
            self.package_logger.log_step(
                "MCP_PARSE_REPO_COMPLETE",
                f"GitHub repository parse complete for URL: {repo_url}",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_PARSE_REPO_FAILED",
                f"GitHub repository parse failed for URL: {repo_url}",
                data={"error": str(e)},
            )
            raise

    @retry_with_backoff()
    async def query_knowledge_graph(self, command: str) -> dict:
        """Query the knowledge graph with a command."""
        self.package_logger.log_step(
            "MCP_QUERY_GRAPH_START",
            f"Starting knowledge graph query: {command}",
        )
        try:
            response = await self._call_mcp_tool_async(
                "crawl4ai-rag",
                "query_knowledge_graph",
                {"command": command},
            )
            self.package_logger.log_step(
                "MCP_QUERY_GRAPH_COMPLETE",
                "Knowledge graph query complete",
                data={"response": response},
            )
            return cast(dict, response)
        except Exception as e:
            self.package_logger.log_step(
                "MCP_QUERY_GRAPH_FAILED",
                f"Knowledge graph query failed: {str(e)}",
                data={"error": str(e)},
            )
            raise

    async def check_infrastructure_health(self) -> Dict[str, Any]:
        """Check the health of MCP infrastructure components."""
        health_status: Dict[str, Any] = {
            "mcp_server": {"status": "unknown", "message": ""},
            "neo4j": {"status": "unknown", "message": ""},
            "supabase": {"status": "unknown", "message": ""},
            "overall": {"status": "unknown", "healthy": False},
        }

        # Check MCP server connectivity
        try:
            # Try a simple MCP call to test connectivity
            await self.get_available_sources()
            health_status["mcp_server"] = {
                "status": "healthy",
                "message": "MCP server responding correctly",
            }
        except Exception as e:
            health_status["mcp_server"] = {
                "status": "unhealthy",
                "message": f"MCP server connection failed: {str(e)}",
            }

        # Check Neo4j (indirectly through knowledge graph query)
        try:
            await self.query_knowledge_graph("repos")
            health_status["neo4j"] = {
                "status": "healthy",
                "message": "Neo4j responding through knowledge graph",
            }
        except Exception as e:
            health_status["neo4j"] = {
                "status": "unhealthy",
                "message": f"Neo4j connection failed: {str(e)}",
            }

        # Supabase health is checked implicitly through MCP server
        if health_status["mcp_server"]["status"] == "healthy":
            health_status["supabase"] = {
                "status": "healthy",
                "message": "Supabase responding through MCP server",
            }
        else:
            health_status["supabase"] = {
                "status": "unknown",
                "message": "Cannot check Supabase - MCP server unavailable",
            }

        # Overall health
        healthy_components = sum(
            1
            for component in ["mcp_server", "neo4j", "supabase"]
            if health_status[component]["status"] == "healthy"
        )

        if healthy_components == 3:
            health_status["overall"] = {
                "status": "healthy",
                "healthy": True,
                "message": "All infrastructure components are healthy",
            }
        elif healthy_components >= 1:
            health_status["overall"] = {
                "status": "degraded",
                "healthy": False,
                "message": f"{healthy_components}/3 infrastructure components are healthy",
            }
        else:
            health_status["overall"] = {
                "status": "unhealthy",
                "healthy": False,
                "message": "No infrastructure components are responding",
            }

        self.package_logger.log_step(
            "MCP_HEALTH_CHECK_COMPLETE",
            f"Infrastructure health check complete: {health_status['overall']['status']}",
            data=health_status,
        )

        return health_status


mcp_service = MCPService()
