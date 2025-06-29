# src/app/services/hallucination_detector.py

"""
Stage 4: Script validation
"""

from ..utils import retry_with_backoff
import re
from typing import Dict, List, Any
from .rag_service import RAGService


class HallucinationDetector:
    def __init__(self) -> None:
        self.rag_service = RAGService()

    @retry_with_backoff()
    def detect(self, script: str) -> Dict[str, Any]:
        """
        Detects potential hallucinations in a PowerShell script.
        Checks for unknown cmdlets and suspicious patterns.
        """
        issues = []
        confidence_score = 1.0

        # Extract cmdlets from the script
        cmdlet_pattern = r"([A-Z][a-zA-Z]*-[A-Z][a-zA-Z]*)"
        found_cmdlets = re.findall(cmdlet_pattern, script)

        # Check for unknown PSADT cmdlets
        unknown_cmdlets = []
        for cmdlet in found_cmdlets:
            if cmdlet.startswith(
                (
                    "Show-ADT",
                    "Start-ADT",
                    "Get-ADT",
                    "Set-ADT",
                    "Test-ADT",
                    "Remove-ADT",
                    "Copy-ADT",
                    "New-ADT",
                    "Stop-ADT",
                )
            ):
                # Query RAG to see if documentation exists
                docs = self.rag_service.query([cmdlet])
                if not docs or f"Documentation for PSADT cmdlets: {cmdlet}" in docs:
                    unknown_cmdlets.append(cmdlet)

        if unknown_cmdlets:
            issues.append(
                {
                    "type": "unknown_cmdlets",
                    "description": f"Unknown PSADT cmdlets found: {', '.join(unknown_cmdlets)}",
                    "severity": "high",
                    "cmdlets": unknown_cmdlets,
                }
            )
            confidence_score -= 0.3

        # Check for suspicious patterns
        suspicious_patterns = [
            (r"Invoke-Expression", "Use of Invoke-Expression can be dangerous"),
            (
                r"Start-Process.*-WindowStyle Hidden",
                "Hidden process execution detected",
            ),
            (r"Remove-Item.*-Recurse.*-Force", "Aggressive file deletion detected"),
        ]

        for pattern, description in suspicious_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append(
                    {
                        "type": "suspicious_pattern",
                        "description": description,
                        "severity": "medium",
                        "pattern": pattern,
                    }
                )
                confidence_score -= 0.1

        has_hallucinations = len(issues) > 0

        return {
            "has_hallucinations": has_hallucinations,
            "confidence_score": max(0.0, confidence_score),
            "issues": issues,
            "total_cmdlets_found": len(found_cmdlets),
            "unknown_cmdlets_count": len(unknown_cmdlets),
            "report": {
                "summary": f"Found {len(issues)} potential issues in the script",
                "recommendations": self._generate_recommendations(issues),
            },
        }

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected issues."""
        recommendations = []

        for issue in issues:
            if issue["type"] == "unknown_cmdlets":
                recommendations.append(
                    f"Verify that the cmdlets {', '.join(issue['cmdlets'])} exist in the PSADT framework"
                )
            elif issue["type"] == "suspicious_pattern":
                recommendations.append(
                    f"Review the use of potentially dangerous patterns: {issue['description']}"
                )

        if not recommendations:
            recommendations.append("No issues detected. Script appears to be valid.")

        return recommendations
