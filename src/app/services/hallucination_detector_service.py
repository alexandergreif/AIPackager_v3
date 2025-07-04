# src/app/services/hallucination_detector_service.py

"""
Stage 4: Hallucination Detection
"""

from typing import Dict, Any, cast
import concurrent.futures
import anyio
from .mcp_service import mcp_service
from ..package_logger import get_package_logger


class HallucinationDetectorService:
    def __init__(self, package_id: str) -> None:
        self.package_logger = get_package_logger(package_id)

    def _run_mcp_in_thread(self, async_func: Any, *args: Any, **kwargs: Any) -> Any:
        """Run async MCP function in a separate thread to avoid asyncio conflicts."""

        async def async_wrapper() -> Any:
            return await async_func(*args, **kwargs)

        def run_async() -> Any:
            return anyio.run(async_wrapper)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result(timeout=30)

    def detect_hallucinations(self, script_path: str) -> Dict[str, Any]:
        """
        Detects hallucinations in a generated script using the crawl4ai-rag MCP server.
        """
        self.package_logger.log_step(
            "HALLUCINATION_DETECTION_START",
            f"Starting hallucination detection for script: {script_path}",
        )
        try:
            report = self._run_mcp_in_thread(
                mcp_service.check_hallucinations, script_path
            )
            self.package_logger.log_step(
                "HALLUCINATION_DETECTION_COMPLETE",
                "Hallucination detection complete",
                data={"report": report},
            )
            return cast(Dict[str, Any], report)
        except Exception as e:
            self.package_logger.log_error(
                "HALLUCINATION_DETECTION_FAILED",
                e,
                context={"script_path": script_path},
            )
            # Return a default report indicating failure
            return {
                "status": "error",
                "issues": [
                    {
                        "type": "detection_failed",
                        "message": str(e),
                    }
                ],
            }
