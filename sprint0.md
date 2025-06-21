# Sprint 0 – Repository & Tooling
**Duration:** 1 week  
**Goal:** Stable repo, dependency locks, automated tests on every push.

| ID | Task | Acceptance |
|----|------|------------|
| SP0‑01 | Initialise git repo & `.gitignore`. | Repo pushed, common ignores committed. |
| SP0‑02 | Add `requirements.in` / `requirements-dev.in`; lock with **pip‑compile**. | `requirements*.txt` reproducible; CI checks diff. |
| SP0‑03 | Configure **pre‑commit** (Ruff, Mypy, Black). | `pre‑commit run --all-files` passes. |
| SP0‑04 | Add **GitHub Actions** CI with pip caching. | Matrix (3.10/3.11) runs Ruff, mypy, pytest. |
| SP0‑05 | Empty Pytest suite scaffold (`tests/`). | `pytest -q` exits 0. |

**DoD** • CI green on `main`; `pre‑commit` installed by all devs.
