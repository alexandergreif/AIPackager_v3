STAGE_ORDER = [
    "upload",
    "extract_metadata",
    "instruction_processing",
    "rag_enrichment",
    "script_generation",
    "hallucination_detection",
    "advisor_correction",
]


def pct(step: str) -> int:
    try:
        return int(STAGE_ORDER.index(step) / (len(STAGE_ORDER) - 1) * 100)
    except ValueError:
        return 0
