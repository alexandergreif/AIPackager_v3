# Sprint 2 – Backend Core
**Duration:** 1 week
**Goal:** Persist uploads, extract metadata, CMTrace logging.

| ID | Task |
|----|------|
| SP2‑01 | ✅ DONE: SQLAlchemy models (`Package`, `Metadata`) + Alembic migration. |
| SP2‑02 | ✅ DONE: File persistence to `instance/uploads/{uuid}_file.ext`. |
| SP2‑03 | ✅ DONE: Metadata extractor: LessMSI for MSI, PE header for EXE. |
| SP2‑04 | ✅ DONE: CMTrace logging helper (`logging_cmtrace.py`). |
| SP2‑05 | ✅ DONE: API route `/api/packages` POST → creates DB entry. |
| SP2‑06 | ✅ DONE: Unit tests: upload & metadata; logging format check. |

**DoD** • Upload call stores file & metadata; log file visible in CMTrace.
