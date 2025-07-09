# Sprint 6 – `crawl4ai-rag` Integration & Tracing
**Duration:** 1 week
**Goal:** Fully integrate `crawl4ai-rag` MCP server for RAG retrieval and Hallucination Checks, ensure Advisor AI gets RAG content, and implement tracing for RAG content.

| ID | Task | Status |
|----|------|--------|
| SP6‑01 | Implement `crawl4ai-rag` Integration in `src/app/services/mcp_service.py` | To Do |
| SP6‑02 | Implement Detailed RAG Content Logging for Stage 2 in `src/app/services/rag_service.py` | To Do |
| SP6‑03 | Verify Advisor AI RAG Integration in `src/app/services/advisor_service.py` | Done |
| SP6‑04 | Verify Hallucination Detector Knowledge Graph Integration in `src/app/services/hallucination_detector_service.py` | Done |
| SP6‑05 | Enhance `crawl4ai-rag` Integration Tests | Done |
| SP6‑06 | (Optional) Persist Stage 2 RAG Content in Database | To Do |
| SP6‑07 | **NEW**: Create Backend API for Knowledge Base Management | To Do |
| SP6‑08 | **NEW**: Develop Frontend UI for Knowledge Base Page | To Do |

## **Task Details**

### SP6‑01: Implement `crawl4ai-rag` Integration in `src/app/services/mcp_service.py`
*   **Description**: Replace mock implementations in `MCPService` with actual `use_mcp_tool` calls.
    *   Update `perform_rag_query`: Replace mock with `use_mcp_tool` for `crawl4ai-rag`'s `perform_rag_query`. Add `source: str = None` parameter and pass it to the MCP tool. Include logging for query input and response.
    *   Add `check_hallucinations(self, script_path: str) -> dict`: Implement this new method using `use_mcp_tool` to call `crawl4ai-rag`'s `check_ai_script_hallucinations`. Include logging for script path input and validation report output.
*   **Files**: `src/app/services/mcp_service.py`

### SP6‑02: Implement Detailed RAG Content Logging for Stage 2 in `src/app/services/rag_service.py`
*   **Description**: Enhance `RAGService.query` to log the exact RAG content retrieved and ensure source filtering.
    *   Modify `query(self, cmdlets: List[str]) -> str`: Pass `source="psappdeploytoolkit.com"` to `mcp_service.perform_rag_query`.
    *   Add detailed logging (e.g., at INFO/DEBUG level) to capture and log the full content returned by the `crawl4ai-rag` server for tracing purposes.
*   **Files**: `src/app/services/rag_service.py`

### SP6‑03: Verify Advisor AI RAG Integration in `src/app/services/advisor_service.py`
*   **Description**: Confirm and, if necessary, update the Advisor AI (Stage 5) to correctly use `RAGService.query` with source filtering for generating corrections.
    *   Read `src/app/services/advisor_service.py` to understand its current RAG interaction.
    *   Ensure it calls `RAGService.query` and that the `psappdeploytoolkit.com` source is used for relevant queries.
*   **Files**: `src/app/services/advisor_service.py` (and potentially `src/app/prompts/` if prompts need adjustment)

### SP6‑04: Verify Hallucination Detector Knowledge Graph Integration in `src/app/services/hallucination_detector_service.py`
*   **Description**: Confirm and, if necessary, update the Hallucination Detector (Stage 4) to use the new `mcp_service.check_hallucinations` method.
    *   Read `src/app/services/hallucination_detector_service.py` to understand its current validation mechanism.
    *   Ensure it calls `mcp_service.check_hallucinations` with the generated PowerShell script path.
*   **Files**: `src/app/services/hallucination_detector_service.py`

### SP6‑05: Enhance `crawl4ai-rag` Integration Tests
*   **Description**: Add comprehensive unit and integration tests for the new `crawl4ai-rag` integrations.
    *   **Unit Tests**: For `MCPService`, `RAGService`, `AdvisorService`, and `HallucinationDetectorService` to mock MCP tool calls and verify correct parameter passing and return value handling.
    *   **Integration Tests**: For the overall pipeline stages (Stage 2, 4, 5) to ensure end-to-end interaction with the `crawl4ai-rag` server (mocking the server if necessary, or using a test instance). Verify source filtering is applied.
*   **Files**: `tests/test_mcp_service.py` (new), `tests/test_rag_service.py` (update), `tests/test_advisor_service.py` (update), `tests/test_hallucination_detector.py` (update), `tests/test_pipeline_full.py` (update)

### SP6‑06: (Optional) Persist Stage 2 RAG Content in Database
*   **Description**: Add a new field to the `Package` model to store the RAG content used in Stage 2 for each pipeline run. This will allow for post-mortem analysis and debugging.
    *   Modify `src/app/models.py` to add a new column (e.g., `rag_content_stage2: str`).
    *   Generate a new Alembic migration script (`alembic revision --autogenerate -m "add_rag_content_field_to_package"`).
    *   Update the relevant service (e.g., `src/app/services/pipeline_service.py` or `src/app/services/rag_service.py`) to save the RAG content to this field.
*   **Files**: `src/app/models.py`, `alembic/versions/`, relevant service file.

### SP6‑07: Create Backend API for Knowledge Base Management
*   **Description**: Create new API endpoints in `src/app/routes.py` to manage the knowledge base.
    *   `POST /api/kb/crawl`: Receives a URL, calls `mcp_service.crawl_and_index(url)`, and returns the status.
    *   `GET /api/kb/sources`: Calls `mcp_service.get_available_sources()` and returns the list of crawled sources.
*   **Files**: `src/app/routes.py`, `src/app/services/mcp_service.py` (add `get_available_sources` method)

### SP6‑08: Develop Frontend UI for Knowledge Base Page
*   **Description**: Create a new "Knowledge Base" page in the UI.
    *   Add a new template (e.g., `src/app/templates/knowledge_base.html`).
    *   Implement a simple form to submit a URL for crawling.
    *   Display a list of current sources fetched from the `/api/kb/sources` endpoint.
    *   Add a link to this new page in the main navigation bar (e.g., in `src/app/templates/base.html`).
*   **Files**: `src/app/templates/knowledge_base.html`, `src/app/templates/base.html`, `src/app/routes.py` (add route to render the page)

## **Out-of-the-Box Considerations (Future Enhancements)**

*   **RAG Data Freshness & Invalidation Strategy**: Explore a "Tools" subpage in the Web UI to display Knowledge Graph/Base content and trigger manual updates.
*   **Knowledge Graph/Database Update Process**: Rely on standard commandlets for now; consider automated updates later.
*   **UI for RAG/KG Insights**: Implement UI elements on the job detail page to inspect RAG content and hallucination reports.
*   **Robust Error Handling for `crawl4ai-rag`**: Ensure robust error handling in code; consider a "restart button" for the MCP server in the UI for quick recovery.

**Definition of Done**: All core integration tasks (SP6-01 to SP6-05) are completed and tested.
