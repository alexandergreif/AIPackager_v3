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

## 2. Knowledge Base Explorer UI with crawl4ai-rag

Let users search or browse the indexed PSADT documentation and code examples used by the RAG system, and show which documentation snippets were retrieved for their package.

**Implementation Approach:**
- Expose a backend API endpoint that proxies queries to the crawl4ai-rag MCP server (e.g., `/api/kb/search?q=Start-ADTProcess`).
- Add a "Knowledge Explorer" page or sidebar in the web app.
- Let users enter search queries, see results (title, snippet, source), and click to view full docs/examples.
- For each package/job, show a "Context Used" tab that lists the exact documentation/code snippets retrieved by RAG for that job.
- When viewing a generated script, display a panel with "Documentation used for this script" (the RAG context that was injected into the prompt).
- Optionally, let users click a snippet to see the full source in the KB explorer.
- Advanced: Use a JS graph library (e.g., Cytoscape.js) to visualize relationships between cmdlets, docs, and examples as nodes/edges from the knowledge graph.

---

## 3. Administrative "Tools" Page

Create a dedicated "Tools" or "Settings" page in the web interface for administrative and maintenance tasks.

**Implementation Approach:**
- Create a new route (e.g., `/tools`) protected by an admin role/permission.
- **Initial Features:**
  - **Cmdlet Reference Management**:
    - Display the currently cached PSADT cmdlet reference.
    - Add a "Refresh Cmdlet Reference" button that manually triggers the `CmdletDiscoveryService` to re-scan the `PSADT/docs` directory. This is useful after updating the PSADT version without restarting the application.
- **Future Enhancements:**
  - **API Key Management**: Securely update and manage API keys for services like OpenAI.
  - **MCP Server Configuration**: View the status of connected MCP servers and manage their settings.
  - **Knowledge Base Management**: Manually trigger re-indexing of the RAG knowledge base.
  - **View Application Logs**: Provide a simple log viewer for troubleshooting.

---

## 4. Hybrid Process Name Detection for `-CloseApps`

Enhance the logic for determining which executables to close before an installation to make it more robust.

**Implementation Approach:**
- **Phase 1 (Current)**: Enhance `MetadataExtractor` to parse the `Icon` and `Shortcut` tables from MSI files to find associated `.exe` names. This provides a reliable, deterministic method.
- **Phase 2 (Future Enhancement)**: Implement an AI-powered fallback. If the MSI parsing fails or returns no results (e.g., for an EXE installer), modify the Stage 1 `InstructionProcessor` to predict the process name.
  - Add a `predicted_processes_to_close` field to the `InstructionResult` schema.
  - Enhance the Stage 1 prompt to ask the AI: "Based on the application name 'X' and installer filename 'Y', what are the likely process names to close (e.g., 'firefox.exe', 'chrome.exe')?"
- The final script rendering logic will use the process names from the database, whether they came from MSI parsing or AI prediction.
