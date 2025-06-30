# src/app/services/hallucination_detector_service.py

"""
Stage 4: Hallucination Detection
"""

from .mcp_service import mcp_service
from ..package_logger import get_package_logger


class HallucinationDetectorService:
    def __init__(self, package_id: str):
        self.package_logger = get_package_logger(package_id)

    def detect_hallucinations(self, script_path: str) -> dict:
        """
        Detects hallucinations in a generated script using the crawl4ai-rag MCP server.
        """
        self.package_logger.log_step(
            "HALLUCINATION_DETECTION_START",
            f"Starting hallucination detection for script: {script_path}",
        )
        try:
            report = mcp_service.check_hallucinations(script_path)
            self.package_logger.log_step(
                "HALLUCINATION_DETECTION_COMPLETE",
                "Hallucination detection complete",
                data={"report": report},
            )
            return report
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
