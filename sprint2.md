# Sprint 2 – Backend Core
**Duration:** 1 week
**Goal:** Persist uploads, extract metadata, CMTrace logging.

| ID | Task |
|----|------|
| SP2‑01 | SQLAlchemy models (`Package`, `Metadata`) + Alembic migration. |
| SP2‑02 | File persistence to `instance/uploads/{uuid}_file.ext`. |
| SP2‑03 | Metadata extractor: LessMSI for MSI, PE header for EXE. |
| SP2‑04 | CMTrace logging helper (`logging_cmtrace.py`). |
| SP2‑05 | API route `/api/packages` POST → creates DB entry. |
| SP2‑06 | Unit tests: upload & metadata; logging format check. |

**DoD** • Upload call stores file & metadata; log file visible in CMTrace.
