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
