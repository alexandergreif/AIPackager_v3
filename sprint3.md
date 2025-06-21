# Sprint 3 – Template & Prompt Layer
**Duration:** 1 week  
**Goal:** Deterministic PSADT template & prompt templates (no AI yet).

| ID | Task |
|----|------|
| SP3‑01 | Add `templates/psadt/Deploy-Application.ps1.j2`. |
| SP3‑02 | Create `templates/prompts/system.j2` & `user.j2`. |
| SP3‑03 | `ScriptRenderer` renders placeholder sections to PS1. |
| SP3‑04 | Snapshot tests: rendered PS1 matches golden file. |
| SP3‑05 | Expose `/api/render/<id>` for manual re‑render. |

**DoD** • Given fixture metadata → rendered script passes compliance linter.
