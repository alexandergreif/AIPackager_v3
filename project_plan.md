# Project Plan – AIPackager v3 (5-Stage Self-Correcting AI Pipeline)

**Document ID:** project_plan.md
**Last updated:** 2025‑06‑24

---

## 1  Purpose & Vision
Deliver a **self-correcting AI-powered web application** that generates production-ready **PowerShell App Deployment Toolkit** scripts through a **5-stage validation pipeline**: Instruction Processing → Targeted RAG → Script Generation → Hallucination Detection → Advisor Correction.

**Innovation**: First PSADT generator with built-in hallucination detection and self-correction capabilities.

## 2  Enhanced Objectives & KPIs

| ID | Objective | Key Metric |
|----|-----------|-----------|
| O1 | Self-correcting AI workflow (Upload → 5-Stage Pipeline → Validated Script) | 85%+ hallucination detection accuracy |
| O2 | Reliable metadata extraction + intelligent cmdlet prediction | ≥ 95% metadata accuracy + 80% cmdlet prediction |
| O3 | **Enhanced**: Self-correcting PSADT script generation | 90%+ scripts pass compliance after advisor correction |
| O4 | Quality gates in CI + pipeline performance | Ruff, mypy, pytest green + <30s total pipeline time |
| O5 | Job resilience with pipeline state recovery | Interrupted jobs auto‑resume from any pipeline stage |

## 3  Enhanced Project Phases

| Phase | Theme | Outcome |
|-------|-------|---------|
| 0 | **Repo & Tooling** | Git, pip‑tools locks, pre‑commit, GitHub Actions |
| 1 | **UI Skeleton** | Upload page, progress bar, sidebar, history list |
| 2 | **Backend Core** | File persistence, DB models, metadata extractor, CMTrace logging |
| 3 | **Multi-Stage Templates** | Enhanced Jinja templates for 5-stage pipeline prompts |
| 4 | **5-Stage AI Pipeline** | Complete self-correcting pipeline with hallucination detection |
| 5 | **Pipeline Optimization** | Performance tuning, metrics, advanced resume logic |

## 4  5-Stage Pipeline Architecture

```
Stage 1: Instruction Processor
├── Input: User instructions + metadata
├── Output: Structured instructions + predicted cmdlets
└── AI Model: GPT-4o (lightweight, fast)

Stage 2: Targeted RAG
├── Input: Predicted cmdlets list
├── Output: Focused PSADT documentation
└── Source: crawl4ai-rag MCP server

Stage 3: Script Generator
├── Input: Structured instructions + documentation
├── Output: Initial PowerShell script
└── AI Model: GPT-4o (full context)

Stage 4: Hallucination Detector
├── Input: Generated PowerShell script
├── Output: Validation report + identified issues
└── Source: crawl4ai-rag knowledge graph

Stage 5: Advisor AI
├── Input: Script + hallucination report
├── Output: Corrected, validated script
└── AI Model: GPT-4o (correction-focused)
```

## 5  Enhanced Risk Register

| Risk | Mitigation | Pipeline-Specific |
|------|------------|-------------------|
| LLM hallucinations | **5-stage validation pipeline + advisor correction** | Built-in detection & correction |
| Pipeline complexity | Graceful degradation + stage-specific error handling | Each stage can fallback |
| Performance impact | Stage caching + parallel processing optimization | <30s total pipeline time |
| RAG data staleness | Selective indexing + pattern-based updates | Knowledge base optimization |

## 6  Success Criteria

### **Pipeline Effectiveness**
- **Hallucination Detection**: >85% accuracy in identifying invalid cmdlets
- **Self-Correction Rate**: >90% of detected issues successfully corrected
- **End-to-End Quality**: >95% of final scripts pass compliance testing
- **Performance**: Complete 5-stage pipeline in <30 seconds

### **Development Efficiency**
- **Token Optimization**: 60-70% reduction through targeted RAG
- **Consistency**: 100% of scripts follow established PSADT patterns
- **Reliability**: Zero undetected hallucinations in production

---

**Enhanced Approval criteria**: All KPIs hit + 5-stage pipeline effectiveness >85% + demo passes end‑to‑end validation.
