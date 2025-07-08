# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
make venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
make install
```

### Running the Application
```bash
# Start Flask development server
make run
# or
python run.py

# Access web interface at http://localhost:5001
```

### Testing
```bash
# Run all tests
make test
# or
.venv/bin/python -m pytest

# Run specific test file
python -m pytest tests/test_metadata_extractor.py -v

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Quality
```bash
# Run linting tools
make lint
# or
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy .
.venv/bin/python -m black --check .

# Fix linting issues
.venv/bin/python -m ruff check --fix .
.venv/bin/python -m black .
```

### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Architecture Overview

AIPackager v3 is a Flask-based web application that generates PowerShell App Deployment Toolkit (PSADT) scripts from MSI/EXE installer files using a 5-stage self-correcting AI pipeline.

### Core Components

#### Web Layer (`src/app/routes.py`)
- **Main Routes**: `/` (landing), `/upload`, `/history`, `/detail/<id>`, `/tools`
- **API Endpoints**: `/api/packages`, `/api/packages/<uuid>/generate`, `/api/health/mcp`
- **Progress Streaming**: `/stream-progress/<id>` for real-time updates

#### 5-Stage AI Pipeline
1. **Instruction Processing**: Converts user instructions to structured commands
2. **Targeted RAG**: Retrieves relevant documentation from knowledge base
3. **Script Generation**: Creates initial PowerShell script using PSADT template
4. **Hallucination Detection**: Validates script against knowledge graph
5. **Advisor Correction**: Self-corrects identified hallucinations

#### Data Models (`src/app/models.py`)
- **Package**: Main entity tracking uploaded files and pipeline state
- **Metadata**: Extracted installer metadata (product name, version, publisher, etc.)

#### Services (`src/app/services/`)
- **`script_generator.py`**: Orchestrates the 5-stage pipeline
- **`mcp_service.py`**: Communicates with crawl4ai-rag MCP server
- **`evaluation_service.py`**: Handles script evaluation and metrics
- **`rag_service.py`**: Manages knowledge base queries

### Key Architecture Patterns

#### Database Session Management
Always use `DatabaseService.get_session()` from `src/app/database.py`. Never instantiate the engine directly.

#### Progress Tracking
The `Package` model tracks pipeline progress through these fields:
- `current_step`: Current pipeline stage
- `progress_pct`: Completion percentage
- `status`: Overall status (uploading, processing, completed, failed)

#### Pipeline State Storage
Each pipeline stage stores its results in the Package model:
- `instruction_result`: Stage 1 output (structured instructions)
- `rag_documentation`: Stage 2 output (retrieved documentation)
- `initial_script`: Stage 3 output (generated script sections)
- `generated_script`: Final script after corrections
- `hallucination_report`: Stage 4 validation results
- `corrections_applied`: Stage 5 corrections

### Knowledge Base Integration

The application integrates with a `crawl4ai-rag` MCP server that provides:
- **PSADT Documentation**: Official cmdlet documentation
- **Knowledge Graph (Neo4j)**: Structural relationships for validation
- **Vector Database (Supabase)**: Embeddings for RAG queries

#### Knowledge Base Source Filtering
All AI-powered generation must use source-based filtering for queries:
- `aipackager-stable`: Internal code patterns (models, DB service)
- `aipackager-ai-patterns`: OpenAI SDK usage and Pydantic schemas
- `aipackager-pipeline`: 5-stage pipeline logic
- `psappdeploytoolkit.com`: PSADT cmdlet documentation
- `flask.palletsprojects.com`: Flask-related questions

## Development Guidelines

### Definition of Done
All work must meet these criteria:
- All CI checks pass (Ruff format/lint, Mypy `--strict`, Pytest)
- Code follows TDD principles
- Database schema changes have Alembic migrations
- Relevant documentation updated

### TDD Workflow
1. Write failing test first
2. Write minimum code to pass
3. Refactor if needed
4. All CI checks must pass (Ruff, Mypy, Pytest)

### Code Quality Standards
- **Type Annotations**: Required for all functions/methods per PEP 484
- **Docstrings**: Google-style for all public modules, classes, functions, and methods
- **Error Handling**: Use specific exceptions (`try...except SpecificError`), never broad `except Exception:`
- **Logging**: Use CMTrace logger (`logging.getLogger(__name__)`) with appropriate levels (DEBUG, INFO, WARNING, ERROR)

### File Organization
```
src/app/
├── routes.py           # Flask routes and API endpoints
├── models.py           # SQLAlchemy data models
├── database.py         # Database session management
├── services/           # Business logic
├── templates/          # Jinja2 HTML templates
├── prompts/            # AI prompts and templates
└── static/             # CSS, JS, images
```

### Environment Variables
- `DATABASE_URL`: Database connection string (default: `sqlite:///instance/aipackager.db`)
- `UPLOAD_FOLDER`: File upload directory
- `MAX_CONTENT_LENGTH`: Upload size limit
- AI service API keys for pipeline operations

**Security**: Never hard-code secrets. All configuration must use environment variables.

## Testing Strategy

### Test Structure
Tests mirror the `src/` structure in `tests/` directory:
- Use fixtures from `conftest.py` for test data
- Mock external dependencies (database, APIs, file system)
- Integration tests use dedicated test database

### Test Categories
- **Unit Tests**: Individual function/class testing
- **Integration Tests**: Component interaction testing
- **Pipeline Tests**: End-to-end workflow testing

## Security Considerations

- **File Uploads**: Validate extensions (.msi, .exe) and size limits
- **XSS Prevention**: All user-provided data properly escaped in templates
- **Secrets Management**: No hardcoded secrets - use environment variables
- **Database Security**: Sessions properly closed via `DatabaseService.get_session()`

## AI Pipeline Guidelines

### 5-Stage Pipeline Implementation
When working with script generation, strictly follow the 5-stage workflow:

1. **Stage 1 (Instruction Processor)**: Focus on predicting required PSADT cmdlets from user input
2. **Stage 2 (Targeted RAG)**: Use source-based filtering to query relevant documentation
3. **Stage 3 (Script Generator)**: Generate initial script using PSADT template structure
4. **Stage 4 (Hallucination Detector)**: Validate against knowledge graph for valid cmdlets/parameters
5. **Stage 5 (Advisor AI)**: Generate corrections based on targeted RAG queries against `psappdeploytoolkit.com`

### Pipeline Completion
A pipeline task is complete only when:
- All 5 stages have successfully finished
- Final script is rendered and stored
- Pipeline state is properly updated in the Package model
