# MCP Integration Implementation Plan
**AIPackager v3 - Tools Page with crawl4ai-rag Integration**

## Overview

This document outlines the complete implementation plan for integrating the `crawl4ai-rag` MCP server with AIPackager v3's Tools page functionality. The integration provides live knowledge base management capabilities including crawling, indexing, and repository parsing.

---

## Infrastructure Requirements

### 1. Neo4j (Knowledge Graph)
- **Purpose**: Store repository structure and code relationships
- **Usage**: Hallucination detection (Stage 4) and advisor corrections (Stage 5)
- **Installation**: Native installation required (Docker not supported with crawl4ai-rag)

```bash
# macOS
brew install neo4j
neo4j start

# Ubuntu/Linux
sudo apt update
sudo apt install neo4j
sudo systemctl start neo4j

# Windows
# Download from https://neo4j.com/download/
# Install Neo4j Desktop or Community Edition
```

### 2. Supabase (Vector Database)
- **Purpose**: Store crawled content embeddings for RAG queries
- **Options**:
  - Supabase Cloud (recommended for production)
  - Local Postgres (development)

### 3. crawl4ai-rag MCP Server
- **Purpose**: Provides crawling, indexing, and knowledge graph tools
- **Installation**: Native Node.js installation required

```bash
npm install -g crawl4ai-rag
crawl4ai-rag --port 8052
```

---

## Configuration Files

### 1. Create `mcp_config.json`

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "type": "sse",
      "url": "http://127.0.0.1:8052/sse",
      "enabled": true,
      "timeout": 60,
      "healthCheck": true,
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_SERVICE_KEY": "${SUPABASE_SERVICE_KEY}",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "${NEO4J_USERNAME}",
        "NEO4J_PASSWORD": "${NEO4J_PASSWORD}",
        "USE_KNOWLEDGE_GRAPH": "true",
        "USE_HYBRID_SEARCH": "true",
        "USE_AGENTIC_RAG": "true",
        "USE_RERANKING": "true"
      }
    }
  }
}
```

### 2. Update `.env.example`

```bash
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4.1-mini

# Supabase (Vector Database)
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Neo4j (Knowledge Graph) - Native Installation
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# MCP Configuration
MCP_CONFIG_PATH=mcp_config.json
```

### 3. Update `requirements.in`

```
# Existing dependencies...

# MCP Integration
mcp>=1.0.0
anyio>=4.0.0
```

---

## Implementation Phases

### Phase 1: Configuration Infrastructure ✅

**Tasks:**
1. Create `mcp_config.json` with server configuration
2. Update `.env.example` with all required variables
3. Create `MCPConfigLoader` class to handle configuration loading
4. Add MCP dependencies to `requirements.in`

**Files to Create/Modify:**
- `mcp_config.json` (new)
- `.env.example` (update)
- `requirements.in` (update)
- `src/app/config.py` (create MCPConfigLoader)

### Phase 2: Enhanced MCPService ✅

**Tasks:**
1. Update `MCPService` to load from `mcp_config.json`
2. Add missing methods for Tools page functionality
3. Add health check capabilities
4. Implement proper error handling and fallbacks

**New Methods to Add:**
```python
async def get_available_sources(self) -> dict
async def crawl_single_page(self, url: str) -> dict
async def smart_crawl_url(self, url: str, max_depth: int = 3, max_concurrent: int = 10, chunk_size: int = 5000) -> dict
async def parse_github_repository(self, repo_url: str) -> dict
async def query_knowledge_graph(self, command: str) -> dict
async def check_infrastructure_health(self) -> dict
```

**Files to Modify:**
- `src/app/services/mcp_service.py` (major update)

### Phase 3: Route Integration ✅

**Tasks:**
1. Replace placeholder implementations in API routes
2. Handle MCP response formats properly
3. Maintain existing frontend interface expectations
4. Add proper error handling for infrastructure failures

**Routes to Update:**
- `api_get_kb_sources()` → Use `mcp_service.get_available_sources()`
- `api_crawl_url()` → Use `mcp_service.crawl_single_page()`
- `api_smart_crawl_url()` → Use `mcp_service.smart_crawl_url()`
- `api_parse_github_repository()` → Use `mcp_service.parse_github_repository()`

**Files to Modify:**
- `src/app/routes.py` (update API endpoints)

### Phase 4: Health Checks & Monitoring ✅

**Tasks:**
1. Add health check endpoint for MCP infrastructure
2. Add service status monitoring
3. Graceful degradation when services unavailable
4. Comprehensive error handling

**New Endpoints:**
- `GET /api/health/mcp` - Check MCP server status
- `GET /api/health/infrastructure` - Check Neo4j, Supabase status

### Phase 5: Documentation & Setup ✅

**Tasks:**
1. Update README with complete setup instructions
2. Create troubleshooting guide
3. Add service management scripts
4. Test complete workflow

---

## Detailed Implementation Steps

### Step 1: MCPConfigLoader Class

```python
# src/app/config.py additions
import json
import os
from pathlib import Path
from typing import Dict, Any

class MCPConfigLoader:
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Environment variable substitution
        return self._substitute_env_vars(config)

    def _substitute_env_vars(self, obj: Any) -> Any:
        # Recursively substitute ${VAR} with environment variables
        pass

    def get_server_config(self, server_name: str) -> Dict[str, Any]:
        return self.config.get("mcpServers", {}).get(server_name, {})
```

### Step 2: Enhanced MCPService

```python
# Key additions to src/app/services/mcp_service.py

class MCPService:
    def __init__(self, package_id: str = "system"):
        self.package_logger = get_package_logger(package_id)
        self.config_loader = MCPConfigLoader()
        self.server_config = self.config_loader.get_server_config("crawl4ai-rag")

    async def get_available_sources(self) -> dict:
        """Get all available sources from the knowledge base."""
        return await self._call_mcp_tool_async(
            "crawl4ai-rag",
            "get_available_sources",
            {}
        )

    async def crawl_single_page(self, url: str) -> dict:
        """Crawl a single page and add to knowledge base."""
        return await self._call_mcp_tool_async(
            "crawl4ai-rag",
            "crawl_single_page",
            {"url": url}
        )

    # Additional methods...
```

### Step 3: Route Updates

```python
# src/app/routes.py updates

@app.route("/api/kb/sources", methods=["GET"])
def api_get_kb_sources() -> Response | tuple[Response, int]:
    """API endpoint to get available knowledge base sources."""
    logger = get_crawl_logger()
    try:
        mcp_service = MCPService()
        sources = anyio.run(mcp_service.get_available_sources)
        logger.info("Successfully retrieved KB sources")
        return jsonify(sources)
    except Exception as e:
        logger.error(f"Failed to get KB sources: {e}")
        return jsonify({"error": "Failed to get knowledge base sources"}), 500
```

---

## Error Handling Strategy

### 1. Infrastructure Availability
- **Neo4j Down**: Disable knowledge graph features, log warning
- **Supabase Down**: Disable RAG queries, use local fallbacks
- **MCP Server Down**: Show clear error messages, suggest restart

### 2. Configuration Issues
- **Missing Config**: Provide default configuration template
- **Invalid Credentials**: Clear error messages with setup instructions
- **Network Issues**: Retry with exponential backoff

### 3. Graceful Degradation
- **Partial Functionality**: Allow basic operations when some services down
- **User Feedback**: Clear status indicators in UI
- **Logging**: Comprehensive logging for troubleshooting

---

## Testing Strategy

### 1. Infrastructure Tests
- Neo4j connectivity
- Supabase connectivity
- MCP server availability
- Configuration loading

### 2. Integration Tests
- End-to-end crawling workflow
- Knowledge base queries
- Repository parsing
- Error handling scenarios

### 3. UI Tests
- Tools page functionality
- Progress indicators
- Error message display
- Source listing accuracy

---

## Setup Documentation for New Users

### Quick Start

```bash
# 1. Install Infrastructure
brew install neo4j node
npm install -g crawl4ai-rag

# 2. Start Services
neo4j start
crawl4ai-rag --port 8052

# 3. Configure Application
cp .env.example .env
# Edit .env with your credentials

# 4. Install Dependencies
pip install -r requirements.txt

# 5. Run Application
python run.py
```

### Detailed Setup Guide

1. **Neo4j Setup**
   - Install Neo4j Community Edition
   - Start Neo4j service
   - Access at http://localhost:7474
   - Change default password from neo4j/neo4j

2. **Supabase Setup**
   - Create account at https://supabase.com
   - Create new project
   - Get URL and service key from project settings

3. **MCP Server Setup**
   - Install Node.js (v18+ recommended)
   - Install crawl4ai-rag globally
   - Start server on port 8052

4. **Application Configuration**
   - Copy `.env.example` to `.env`
   - Fill in all required credentials
   - Verify `mcp_config.json` settings

5. **Verification**
   - Visit `/api/health/mcp` endpoint
   - Check Tools page functionality
   - Test crawling a simple URL

---

## Troubleshooting Guide

### Common Issues

1. **MCP Server Connection Failed**
   - Verify crawl4ai-rag is running on port 8052
   - Check firewall settings
   - Verify environment variables

2. **Neo4j Connection Issues**
   - Ensure Neo4j is running
   - Check bolt://localhost:7687 accessibility
   - Verify credentials in .env

3. **Supabase Authentication Failed**
   - Check SUPABASE_URL format
   - Verify SUPABASE_SERVICE_KEY is correct
   - Test connection manually

4. **Tools Page Not Working**
   - Check browser console for errors
   - Verify API endpoints respond correctly
   - Check MCP server logs

---

## Success Metrics

### Immediate (Post-Implementation)
- ✅ MCP server connects successfully
- ✅ Tools page loads without errors
- ✅ Can retrieve available sources
- ✅ Can crawl and index test URL
- ✅ Health checks pass

### Short-term (1-2 weeks)
- ✅ 5-stage pipeline uses knowledge graph for validation
- ✅ Repository parsing works correctly
- ✅ RAG queries return relevant results
- ✅ Error handling works as expected

### Medium-term (1 month)
- ✅ Knowledge base contains useful development patterns
- ✅ Script generation quality improved
- ✅ Token usage reduced through targeted RAG
- ✅ Setup process streamlined for new users

---

## Next Steps After Implementation

1. **Content Population**
   - Index AIPackager repository structure
   - Crawl PSADT documentation
   - Add Flask and Pydantic documentation

2. **Pipeline Integration**
   - Update hallucination detection to use knowledge graph
   - Enhance advisor service with graph-based corrections
   - Implement source-based RAG filtering

3. **UI Enhancements**
   - Add source management interface
   - Implement crawl progress indicators
   - Add knowledge base statistics

4. **Documentation & Training**
   - Create video setup guides
   - Document best practices
   - Build troubleshooting database

---

This implementation plan provides a complete roadmap for integrating live MCP functionality into the AIPackager v3 Tools page while maintaining compatibility with existing systems and ensuring easy setup for new users.
