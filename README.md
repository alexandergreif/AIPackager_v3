# AIPackager v3: PSADT Script Generator

A Flask web application that generates PowerShell App Deployment Toolkit (PSADT) scripts from Windows installer files using AI-assisted analysis and rule-based validation.

## Overview

AIPackager v3 automates the creation of PSADT deployment scripts by:
- Extracting metadata from MSI/EXE installer files
- Processing user instructions with AI to predict required deployment tasks
- Generating PowerShell scripts using PSADT v4 cmdlets and templates
- Validating generated scripts against PSADT documentation to catch errors

## Architecture

### 5-Stage Processing Pipeline

The application processes uploads through a structured pipeline:

1. **Instruction Processing**: Converts user requirements into structured commands using OpenAI's API
2. **Documentation Retrieval**: Queries knowledge base for relevant PSADT documentation 
3. **Script Generation**: Creates PowerShell script sections using AI and Jinja2 templates
4. **Script Validation**: Checks generated cmdlets and parameters against PSADT v4 documentation
5. **Error Correction**: Applies fixes for validation issues using targeted documentation queries

### Core Components

- **Web Interface**: Flask routes for file upload, progress tracking, and script review
- **Metadata Extraction**: Automatic parsing of MSI/EXE properties and version info
- **AI Integration**: OpenAI API calls for instruction processing and script generation
- **Validation Engine**: Rule-based checking against comprehensive PSADT cmdlet database
- **Progress Tracking**: Real-time pipeline status updates via Server-Sent Events

### Knowledge Base Integration

The application integrates with a `crawl4ai-rag` MCP server that provides:
- PSADT v4 cmdlet documentation and examples
- Vector database for documentation similarity search
- Knowledge graph for code structure validation

## Technical Stack

- **Backend**: Python 3.12+ with Flask 2.3+
- **Database**: SQLAlchemy with SQLite (configurable to PostgreSQL)
- **AI**: OpenAI API integration for text processing
- **Templates**: Jinja2 for script generation and web UI
- **Validation**: Custom parser for PSADT v4 MDX documentation
- **Frontend**: HTML/CSS/JavaScript with real-time updates

## Features

### Script Generation
- Automatic detection of installation/uninstallation requirements
- Template-based PowerShell script structure
- Support for MSI and EXE installer types
- Process closure prediction for application updates

### Validation & Quality Control
- Comprehensive PSADT v4 cmdlet validation (100+ cmdlets supported)
- Parameter type and value checking
- Detection of suspicious PowerShell patterns
- Suggestions for similar/correct cmdlets when errors are found

### User Interface
- Drag-and-drop file upload
- Real-time progress tracking during script generation
- Package history and management
- Detailed script preview with syntax highlighting
- Health monitoring for external services

## Installation & Setup

### Prerequisites
- Python 3.12 or higher
- OpenAI API key for AI processing
- Optional: MCP server for enhanced knowledge base features

### Quick Start

```bash
# Clone and setup environment
git clone <repository-url>
cd AIPackager_v3
make venv && source .venv/bin/activate
make install

# Configure environment
cp .env.example .env
# Add your OpenAI API key to .env

# Initialize database
alembic upgrade head

# Run application
make run
# Access at http://localhost:5001
```

### Configuration

Set environment variables in `.env`:
- `OPENAI_API_KEY`: Required for AI processing
- `DATABASE_URL`: Database connection (default: SQLite)
- `UPLOAD_FOLDER`: File storage location
- `MCP_SERVER_URL`: Optional MCP server endpoint

## Development

### Testing
```bash
# Run test suite
make test

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Quality
```bash
# Linting and formatting
make lint

# Type checking
python -m mypy .
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## API Reference

### Package Management
- `POST /api/packages` - Create new package from uploaded file
- `GET /api/packages` - List all packages
- `POST /api/packages/<uuid>/generate` - Start script generation
- `GET /api/packages/<uuid>` - Get package details

### Health Monitoring
- `GET /api/health/mcp` - Check MCP server connectivity
- `GET /api/health` - Overall application health

### Progress Tracking
- `GET /stream-progress/<uuid>` - Server-sent events for real-time updates

## Validation Details

The script validation system checks for:
- **Unknown Cmdlets**: Flags cmdlets not found in PSADT v4 documentation
- **Invalid Parameters**: Verifies parameter names against cmdlet specifications
- **Parameter Values**: Validates enum values and type constraints
- **Suspicious Patterns**: Detects potentially dangerous PowerShell constructs
- **Best Practices**: Ensures adherence to PSADT coding standards

## Limitations

- Requires internet connectivity for AI processing (OpenAI API)
- Script validation is based on PSADT v4 documentation accuracy
- Complex installer scenarios may require manual script review
- MCP server integration is optional but recommended for full features

## Contributing

1. Follow test-driven development practices
2. Ensure all tests pass: `make test`
3. Run code quality checks: `make lint`
4. Update documentation for new features
5. Create Alembic migrations for database schema changes

## License

See LICENSE file for details.

---

*A practical tool for automating PSADT script creation with AI assistance and comprehensive validation.*
