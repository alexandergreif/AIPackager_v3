# Sprint 4 – 5-Stage Self-Correcting AI Pipeline
**Duration:** 1 week
**Goal:** Complete 5-stage pipeline: Instruction Processing → RAG → Generation → Hallucination Detection → Advisor Correction.

## **5-Stage Pipeline Architecture**

| Stage | Component | Description |
|-------|-----------|-------------|
| 1 | **Instruction Processor** | Convert user text → structured instructions + predicted cmdlets |
| 2 | **Targeted RAG** | Query specific PSADT documentation for predicted cmdlets |
| 3 | **Script Generator** | Generate initial PowerShell script with focused documentation |
| 4 | **Hallucination Detector** | Use crawl4ai-rag to validate script accuracy |
| 5 | **Advisor AI** | Self-correct hallucinations with targeted RAG fixes |

## **Sprint 4 Tasks**

| ID | Task |
|----|------|
| SP4‑01 | Integrate OpenAI SDK, load key from env. |
| SP4‑02 | Define `PSADTScript` Pydantic schema + `InstructionResult` schema for Stage 1. |
| SP4‑03 | Implement **5-Stage PSADTGenerator** service with retry/backoff. |
| SP4‑04 | Update `/api/packages/<id>/generate` to use 5-stage pipeline, store JSON. |
| SP4‑05 | Unit tests with mocked 5-stage pipeline responses. |
| SP4‑06 | **Enhanced**: Set up RAG knowledge base for Stages 2+5 (targeted documentation). |
| SP4‑07 | **NEW**: Implement `InstructionProcessor` (Stage 1) with cmdlet prediction. |
| SP4‑08 | **NEW**: Implement `AdvisorService` (Stage 5) with hallucination correction. |

## **New Service Architecture**
```
src/services/
├── script_generator.py         # 5-stage pipeline orchestrator
├── instruction_processor.py    # Stage 1: User instruction processing
├── rag_service.py             # Stage 2+5: Targeted documentation queries
├── hallucination_detector.py  # Stage 4: Script validation
└── advisor_service.py         # Stage 5: Self-correction AI
```

## **Enhanced Pydantic Schemas**
```python
class InstructionResult(BaseModel):
    """Stage 1 output: structured instructions + predicted cmdlets."""
    structured_instructions: Dict[str, Any]
    predicted_cmdlets: List[str]
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
```

**Enhanced DoD** • 5-stage pipeline returns validated, self-corrected PSADT script → hallucination detection passes → advisor corrections logged.
