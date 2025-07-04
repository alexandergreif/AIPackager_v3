# AIPackager v3 - Tools Page Implementation Plan

This document outlines the detailed plan for implementing the "Tools" page functionality, including integration with the `crawl4ai-rag` MCP server.

---

## Current Status

The frontend UI for the "Tools" page (`src/app/templates/tools.html`) and the backend API endpoints (`src/app/routes.py`) are in place. However, the backend currently uses placeholder data and simulated calls instead of live interactions with the `crawl4ai-rag` MCP server. There was also a minor bug in the frontend displaying `undefined` for source IDs, which has been addressed.

---

## Implementation Plan

The following steps will be taken to fully integrate the "Tools" page with the `crawl4ai-rag` MCP server:

### Phase 1: Frontend Fixes (Completed)

*   **Fix `undefined` Source ID Display**:
    *   **Status**: ✅ Done
    *   **Description**: Corrected the JavaScript in `src/app/templates/tools.html` to properly access `source.source_id` instead of `source.id` when displaying available knowledge base sources.

### Phase 2: Live MCP Integration (Pending)

This phase involves replacing all simulated MCP calls in `src/app/routes.py` with actual calls to the `crawl4ai-rag` MCP server using the existing `MCPService`.

*   **1. Update `api_get_kb_sources` for Live Data**:
    *   **Status**: ⏳ Pending
    *   **File**: `src/app/routes.py`
    *   **Action**: Replace the hardcoded list of sources with a live call to `mcp_service.get_available_sources()`.
    *   **Details**:
        *   Import `MCPService` from `src/app/services/mcp_service.py`.
        *   Instantiate `MCPService` within the `api_get_kb_sources` function.
        *   Call `mcp_service.get_available_sources()` and return its result.

*   **2. Update `api_crawl_url` for Live Crawl**:
    *   **Status**: ⏳ Pending
    *   **File**: `src/app/routes.py`
    *   **Action**: Replace the simulated `crawl_task` with a live call to `mcp_service.crawl_and_index_url()`.
    *   **Details**:
        *   Instantiate `MCPService`.
        *   Call `mcp_service.crawl_and_index_url(url=url)`.
        *   Handle the response and progress updates from the live MCP call.

*   **3. Update `api_smart_crawl_url` for Live Smart Crawl**:
    *   **Status**: ⏳ Pending
    *   **File**: `src/app/routes.py`
    *   **Action**: Replace the simulated `smart_crawl_task` with a live call to `mcp_service.smart_crawl_url()`.
    *   **Details**:
        *   Instantiate `MCPService`.
        *   Call `mcp_service.smart_crawl_url(url=url, max_depth=3, max_concurrent=10, chunk_size=5000)`.
        *   Handle the response and progress updates.

*   **4. Update `api_parse_github_repository` for Live GitHub Parsing**:
    *   **Status**: ⏳ Pending
    *   **File**: `src/app/routes.py`
    *   **Action**: Replace the simulated `parse_github_task` with a live call to `mcp_service.parse_github_repository()`.
    *   **Details**:
        *   Instantiate `MCPService`.
        *   Call `mcp_service.parse_github_repository(repo_url=url)`.
        *   Handle the response and progress updates.

---

## Testing Strategy

After implementing the live MCP calls, the following tests will be performed:

1.  **Verify Available Sources**:
    *   Navigate to the "Tools" page.
    *   Click "Get Available Sources".
    *   Confirm that the displayed sources are accurate and reflect the actual content of the `crawl4ai-rag` knowledge base.

2.  **Test Single URL Crawl**:
    *   Enter a new URL (e.g., `https://devdocs.io/javascript/`) into the "Crawl a URL" input.
    *   Click "Crawl".
    *   Monitor the progress bar and logs.
    *   After completion, click "Get Available Sources" again to confirm the new URL has been added to the list.

3.  **Test GitHub Repository Parse**:
    *   Enter a GitHub repository URL (e.g., a small Python repository) into the "Crawl a GitHub Repository" input.
    *   Click "Parse Repository".
    *   Monitor the progress bar and logs.
    *   After completion, click "Get Available Sources" to confirm the repository's source has been added.

---

## Next Steps

Once the user confirms the plan, I will proceed to Act mode to implement Phase 2.
