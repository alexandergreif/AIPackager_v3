# src/app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class InstructionResult(BaseModel):
    """Stage 1 output: structured instructions + predicted cmdlets."""

    structured_instructions: Dict[str, Any]
    predicted_cmdlets: List[str]
    predicted_processes_to_close: Optional[List[str]] = None
    confidence_score: float


class PSADTScript(BaseModel):
    """Stage 3+5 output: validated PowerShell script sections."""

    pre_installation_tasks: List[str]
    installation_tasks: List[str]
    post_installation_tasks: List[str]
    uninstallation_tasks: List[str]
    post_uninstallation_tasks: List[str]
    hallucination_report: Optional[Dict[str, Any]] = None
    corrections_applied: Optional[List[str]] = None
