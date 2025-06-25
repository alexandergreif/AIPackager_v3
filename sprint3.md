# Sprint 3 – Enhanced Template & Multi-Stage Prompt Layer
**Duration:** 1 week
**Goal:** Multi-stage prompt templates and PSADT rendering foundation for 5-stage AI pipeline.

| ID | Task |
|----|------|
| SP3‑01 | ✅ Add `templates/psadt/Invoke-AppDeployToolkit.ps1.j2`. |
| SP3‑02 | ✅ Create multi-stage prompt templates: `system.j2`, `user.j2`, `instruction_processing.j2`, `advisor_correction.j2`. |
| SP3‑03 | ✅ Enhanced `ScriptRenderer` with pipeline-ready rendering (Stages 3+5). |
| SP3‑04 | ✅ Snapshot tests: rendered PS1 matches golden file with multi-stage structure. |
| SP3‑05 | ✅ Expose `/api/render/<id>` for manual re‑render with pipeline preview. |
| SP3‑06 | ✅ **NEW**: Foundation for instruction processing prompts (Stage 1 prep). |

**Enhanced DoD** • Multi-stage prompt structure ready for 5-stage pipeline → rendered script passes compliance linter.
