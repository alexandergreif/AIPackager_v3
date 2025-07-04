# Additional Feature Ideas for AIPackager

## 1. Custom Prompt Tuning via MCP

Allow advanced users to tweak the AI prompt templates for their job (e.g., add extra requirements, change logging style) and save/reuse custom prompt profiles.

**Implementation Approach:**
- Add a "prompt_profile" field to the package/job model.
- Expose a UI for advanced users to edit and save prompt templates (with validation).
- When calling the AI, the MCP loads the prompt from the profile (or falls back to the default).
- Users can save, name, and reuse prompt profiles for future jobs.
- Optionally, allow users to "fork" a prompt profile from a previous job, tweak it, and re-run the pipeline.

---

## 2. Knowledge Base Explorer UI with crawl4ai-rag ✅ PARTIALLY COMPLETE

Let users search or browse the indexed PSADT documentation and code examples used by the RAG system, and show which documentation snippets were retrieved for their package.

**Implementation Approach:**
- ✅ Expose a backend API endpoint that proxies queries to the crawl4ai-rag MCP server (e.g., `/api/kb/search?q=Start-ADTProcess`).
- ✅ Add a "Knowledge Explorer" page or sidebar in the web app.
- ✅ Let users enter search queries, see results (title, snippet, source), and click to view full docs/examples.
- ⏳ For each package/job, show a "Context Used" tab that lists the exact documentation/code snippets retrieved by RAG for that job.
- ⏳ When viewing a generated script, display a panel with "Documentation used for this script" (the RAG context that was injected into the prompt).
- ⏳ Optionally, let users click a snippet to see the full source in the KB explorer.
- ⏳ Advanced: Use a JS graph library (e.g., Cytoscape.js) to visualize relationships between cmdlets, docs, and examples as nodes/edges from the knowledge graph.

**Status**: Core functionality implemented via Tools page with crawl4ai-rag integration. Advanced features like context tracking and graph visualization remain for future enhancement.

---

## 3. Administrative "Tools" Page ✅ COMPLETE

Create a dedicated "Tools" or "Settings" page in the web interface for administrative and maintenance tasks.

**Implementation Approach:**
- ✅ Create a new route (e.g., `/tools`) protected by an admin role/permission.
- **Initial Features:**
  - ✅ **Knowledge Base Management**:
    - Get Available Sources from crawl4ai-rag
    - Quick Crawl for single pages
    - Smart Crawl with advanced options (depth, concurrent, chunk size)
    - GitHub Repository Parsing for knowledge graph
    - Real-time progress monitoring via SocketIO
  - ✅ **MCP Server Health Monitoring**: Check infrastructure health status
- **Future Enhancements:**
  - ⏳ **Cmdlet Reference Management**: Display cached PSADT cmdlet reference and refresh functionality
  - ⏳ **API Key Management**: Securely update and manage API keys for services like OpenAI
  - ⏳ **Advanced MCP Server Configuration**: View detailed status of connected MCP servers and manage their settings
  - ⏳ **View Application Logs**: Provide a simple log viewer for troubleshooting

**Status**: Core Tools page implemented with comprehensive knowledge base management and MCP integration. Advanced administrative features remain for future enhancement.

---

## 4. Hybrid Process Name Detection for `-CloseApps`

Enhance the logic for determining which executables to close before an installation to make it more robust.

**Implementation Approach:**
- **Phase 1 (Current)**: Enhance `MetadataExtractor` to parse the `Icon` and `Shortcut` tables from MSI files to find associated `.exe` names. This provides a reliable, deterministic method.
- **Phase 2 (Future Enhancement)**: Implement an AI-powered fallback. If the MSI parsing fails or returns no results (e.g., for an EXE installer), modify the Stage 1 `InstructionProcessor` to predict the process name.
  - Add a `predicted_processes_to_close` field to the `InstructionResult` schema.
  - Enhance the Stage 1 prompt to ask the AI: "Based on the application name 'X' and installer filename 'Y', what are the likely process names to close (e.g., 'firefox.exe', 'chrome.exe')?"
- The final script rendering logic will use the process names from the database, whether they came from MSI parsing or AI prediction.

---

## 5. Website Improvement Tasks

**Actionable Tasks**:
- Enhance navigation for better usability.
- Improve responsiveness for mobile and tablet devices.
- Update styling to align with modern design principles.
- Add interactive elements to improve user engagement.

---

## 6. Documentation Update Tasks

**Actionable Tasks**:
- Update API reference with new endpoints and features.
- Revise contributing guidelines to reflect current workflows.
- Enhance deployment guide with detailed steps for production and cloud setups.
- Expand knowledge base implementation plan with recent updates.
- Refine workflow diagram to include enhanced pipeline stages.

---

## 7. Installation Guide Creation Tasks

**Actionable Tasks**:
- Draft installation guide based on 'deployment.md' and 'contributing.md'.
- Validate steps through testing on different environments.
- Add visuals and examples for clarity.

---

## 8. Refining Tasks in 'additional-tasks.md'

**Actionable Tasks**:
- Refine descriptions and implementation approaches for each task.
- Add new tasks if gaps are identified during the review.
- Save updated tasks in 'additional-tasks.md'.

---

## 9. Custom PowerShell Validation MCP Server

Create a dedicated MCP server that integrates the proven deterministic PowerShell validator into the MCP ecosystem for unified validation interface.

**Implementation Approach:**
- Create new `aipackager-validation` MCP server with PowerShell-specific validation tools
- Port existing `HallucinationDetector` logic to MCP server context
- Add auto-detection for script types (Python vs PowerShell)
- Integrate PSADT v4 cmdlet database access within MCP server
- Maintain compatibility with existing `check_ai_script_hallucinations` interface
- Replace current MCP bypass logic with native MCP calls
- Add configuration to switch between local validation and MCP validation

**Benefits:**
- Unified validation interface across all script types
- Better integration with Tools page and knowledge base management
- Potential for extending to other script languages in the future
- Consistent MCP-based architecture throughout the application

**Priority**: Future enhancement (post-MVP)

**Current Status**: The deterministic PowerShell validator is working well as a local fallback. This enhancement would move it to the MCP ecosystem for better architectural consistency.
