# Sprint 2-5 – Workflow Refinement & Detailed Views

> **Purpose:** extend the working backend (Sprint 2) into a user-friendly, fully-tracked workflow with metadata, detailed pages, history navigation, and robust logging.
> **Guideline:** *KISS* — each ticket ≤ 1-2 commits, test-first.

---

## General Rules for this Sprint

1. **Always fetch the latest docs** for every library/tool you touch (Flask, SQLAlchemy, LessMSI, etc.).
2. **Synchronise the crawl4ai-rag knowledge-graph** with those docs before coding—run the repo-parser if versions changed.
3. While coding, **query the knowledge-graph** for class / method signatures instead of guessing.
4. **Run the built-in hallucination-checker** on every new or modified file; PRs must be free of invalid symbols.

These rules apply to *every* ticket below.

---

## Tickets

| ID | Area | Task (smallest possible step) | Acceptance Criteria |
|----|------|------------------------------|---------------------|
| **SP2-5-01** | UI | ✅ DONE: Add **landing page** (`/`) with project summary + “Get Started” button. | Route returns 200; link visible in sidebar. |
| **SP2-5-02** | UI | ✅ DONE: Extend **base template**: fixed sidebar (links Home | Upload | History). | Sidebar appears on every page; active link highlighted. |
| **SP2-5-03** | UI | ✅ DONE: Restrict `/upload` file chooser to `.msi,.exe`. | Invalid types blocked client & server side; flash error shown. |
| **SP2-5-04** | Backend | ✅ DONE: Add **textarea** for user notes on `/upload`; persist to DB (`Package.notes`). | Notes appear on detail page. |
| **SP2-5-05** | Backend | ✅ DONE: Implement **OOP class `PackageRequest`** (`src/aipackager/workflow.py`) wrapping SQLAlchemy row; helpers `start()`, `set_step()`, `save_metadata()`. | Unit tests confirm DB sync + helper behaviour. |
| **SP2-5-06** | Backend | ✅ DONE: Create **enum `WorkflowStep`** (`UPLOAD`, `EXTRACT_METADATA`, `PREPROCESS`, `GENERATE_PROMPT`, `CALL_AI`, `RENDER_SCRIPT`, `COMPLETED`, `FAILED`) and add columns `current_step`, `progress_pct`. | Alembic migration; progress bar streams step name. |
| **SP2-5-07** | Metadata | ✅ DONE: Expand extractor to capture PSADT vars: `appName`, `appVersion`, `vendor`, `productCode`. | Values stored in `Metadata`; unit test parses sample MSI. |
| **SP2-5-08** | Logging | ✅ DONE: Add **packages.log** (global). On each `PackageRequest.set_step()` write CMTrace line: `<timestamp> | <package_id> | <old_step> -> <new_step>`. Unit test asserts line append. |
| **SP2-5-09** | UI | ✅ DONE: Build **detail view** (`/detail/<uuid>`) showing summary card, full metadata table, and rendered script in `<pre>` with Copy / Download buttons. | Copy places script on clipboard. |
| **SP2-5-10** | UI | ✅ DONE: **History page**: list last 90 days (date, name, version, status). | Row click loads matching detail view. |
| **SP2-5-11** | Resume | On app start, resume packages not `COMPLETED`/`FAILED` via `PackageRequest.resume_pending_jobs()`. | Integration test: crash mid-workflow, restart completes job. |
| **SP2-5-12** | Docs | Update `README` + `/docs`: new pages, workflow diagram, GIF of progress bar; `markdownlint` passes. | CI green. |

---

## Later / Backlog

* Silent-switch discovery for `.exe` installers.
* Replace Tailwind CDN with npm `tailwindcss-cli` build + purge.

---
