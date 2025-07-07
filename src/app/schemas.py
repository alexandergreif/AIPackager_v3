# src/app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class InstructionResult(BaseModel):
    """Stage 1 output: structured instructions + predicted cmdlets."""

    structured_instructions: Dict[str, Any]
    predicted_cmdlets: List[str]
    confidence_score: float
    predicted_processes_to_close: Optional[List[str]] = None


class PSADTScript(BaseModel):
    """Stage 3+5 output: validated PowerShell script sections."""

    pre_installation_tasks: List[str]
    installation_tasks: List[str]
    post_installation_tasks: List[str]
    uninstallation_tasks: List[str]
    post_uninstallation_tasks: List[str]
    pre_repair_tasks: List[str]
    repair_tasks: List[str]
    post_repair_tasks: List[str]
    hallucination_report: Optional[Dict[str, Any]] = None
    corrections_applied: Optional[List[Dict[str, Any]]] = None


# --- Evaluation Feature Schemas ---


class Scenario(BaseModel):
    """Pydantic model for a test scenario."""

    id: str
    title: str
    prompt: str
    difficulty: str
    category: str
    psadt_variables: Dict[str, str]


class ModelInfo(BaseModel):
    """Pydantic model for a language model."""

    id: str
    name: str
    description: str


class EvaluationMetrics(BaseModel):
    """Pydantic model for evaluation metrics."""

    hallucinations_found: int
    hallucinations_corrected: int
    trust_score: float


class EvaluationResult(BaseModel):
    """Pydantic model for a full evaluation result."""

    id: str
    model: ModelInfo
    scenario: Scenario
    timestamp: str
    raw_model_output: str
    advisor_corrected_output: str
    evaluation_log: str  # This will now be a path to the log file
    metrics: EvaluationMetrics
    detailed_hallucination_report: Optional[List[Dict[str, Any]]] = None
    detailed_corrections_log: Optional[List[Dict[str, Any]]] = None
