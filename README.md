# AIPackager v3

A web application that generates PowerShell App Deployment Toolkit (PSADT) scripts from Windows installer files using AI.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Git
- Optional: `msitools` for enhanced MSI metadata extraction

### Environment Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd AIPackager_v3
   make venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   make install
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   - Edit the `.env` file and add your OpenAI API key.
   - **For full AI capabilities (5-stage pipeline, knowledge base), you will also need to set up Neo4j, Supabase, and the `crawl4ai-rag` MCP server.** Refer to the [Deployment Guide](docs/deployment.md) for detailed instructions.

3. **Run the application:**
   ```bash
   python run.py
   ```

4. **Access the web interface:**
   Open http://localhost:5001 in your browser

## 📋 Features

### ✅ Completed Features

- **5-Stage Self-Correcting Pipeline**: Automated script generation with instruction processing, targeted RAG, script generation, hallucination detection, and advisor correction.
- **Web Interface**: Clean, responsive UI with Tailwind CSS and real-time progress updates.
- **File Upload**: Support for MSI and EXE installer files.
- **Metadata Extraction**: Advanced MSI metadata extraction using msitools.
- **Workflow Tracking**: Step-by-step progress tracking with CMTrace logging.
- **History Management**: View and manage previous package processing jobs.

### 🔄 Workflow Steps

1. **Upload** - Select MSI/EXE installer file.
2. **Metadata Extraction** - Parse installer metadata.
3. **Stage 1: Instruction Processing** - Convert user input to structured instructions.
4. **Stage 2: Targeted RAG** - Query documentation for relevant context.
5. **Stage 3: Script Generation** - Generate the initial PowerShell script.
6. **Stage 4: Hallucination Detection** - Validate the script against a knowledge graph.
7. **Stage 5: Advisor Correction** - Self-correct any identified hallucinations.
8. **Completed** - Download or copy the generated script.

## 🏗️ Architecture

```
AIPackager_v3/
├── src/
│   ├── app/                    # Flask application
│   │   ├── templates/          # Jinja2 HTML templates
│   │   ├── models.py          # SQLAlchemy database models
│   │   ├── routes.py          # Flask route handlers
│   │   ├── database.py        # Database service layer
│   │   ├── metadata_extractor.py  # MSI/EXE metadata extraction
│   │   ├── logging_cmtrace.py # CMTrace format logging
│   │   └── file_persistence.py    # File upload handling
│   └── aipackager/
│       └── workflow.py        # Business logic & workflow management
├── tests/                     # Comprehensive test suite
├── alembic/                   # Database migrations
├── docs/                      # Documentation
└── instance/                  # Runtime data (uploads, database)
```

## 🗃️ Database Schema

### Package Model
- **id**: UUID primary key
- **filename**: Original installer filename
- **file_path**: Stored file location
- **upload_time**: Timestamp of upload
- **status**: Current processing status (`uploading`, `processing`, `completed`, `failed`)
- **current_step**: Current workflow step (e.g., `instruction_processing`, `targeted_rag`)
- **progress_pct**: Completion percentage
- **custom_instructions**: User-provided notes
- **instruction_result**: JSON object with structured instructions and predicted cmdlets (Stage 1 output).
- **rag_documentation**: String with documentation retrieved from RAG (Stage 2 output).
- **initial_script**: JSON object with the initial generated script sections (Stage 3 output).
- **generated_script**: JSON object with the final generated script sections (after Stage 5 correction if applicable).
- **hallucination_report**: JSON object with the hallucination detection results (Stage 4 output).
- **pipeline_metadata**: JSON object with metadata about the pipeline execution (e.g., model used, version).
- **corrections_applied**: List of strings detailing corrections applied by the advisor (Stage 5 output).

### Metadata Model
- **package_id**: Foreign key to Package
- **product_name**: Extracted product name
- **version**: Product version
- **publisher**: Software publisher/manufacturer
- **install_date**: Installation date string
- **uninstall_string**: Command string for uninstallation
- **estimated_size**: Estimated size of the application in bytes
- **product_code**: MSI Product Code GUID
- **upgrade_code**: MSI Upgrade Code GUID
- **language**: Installation language
- **architecture**: Target architecture (x86/x64/arm64)
- **executable_names**: List of executable names found within the installer.

## 🧪 Development

### Testing
```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_metadata_extractor.py -v

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Quality
```bash
# Linting and formatting
make lint

# Pre-commit hooks (runs automatically)
ruff check --fix
black .
mypy src/
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

## 📊 Sprint Progress

- ✅ **Sprint 0**: Repository & Tooling Setup
- ✅ **Sprint 1**: UI Skeleton & Basic Routes
- ✅ **Sprint 2**: Backend Core & Database Models
- ✅ **Sprint 2-5**: Workflow Refinement & Detailed Views
- ✅ **Sprint 3**: Template & Prompt Engineering
- ✅ **Sprint 4**: AI Integration with 5-Stage Pipeline
- ✅ **Sprint 5**: Hallucination Detection & Advisor Correction

### Sprint 2-5 Achievements (Current)

| Feature | Status | Description |
|---------|--------|-------------|
| Landing Page | ✅ | Project overview with navigation |
| File Upload | ✅ | MSI/EXE file upload with validation |
| Metadata Extraction | ✅ | Advanced MSI parsing with msitools |
| Workflow Tracking | ✅ | Step-by-step progress with enum states |
| Resume Functionality | ✅ | Auto-resume interrupted workflows |
| History Management | ✅ | View past processing jobs |
| Detail Views | ✅ | Comprehensive package information |
| CMTrace Logging | ✅ | Structured logging for monitoring |

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: Custom database connection string
- `UPLOAD_FOLDER`: Custom upload directory
- `MAX_CONTENT_LENGTH`: File upload size limit

### Development Rules (.clinerules)
- **TDD**: Test-first development approach
- **KISS**: Keep It Simple, Stupid principle
- **Branching**: Feature branches with PR reviews
- **Quality Gates**: Ruff, mypy, pytest must pass

## 📚 Documentation

See the [docs/](docs/) directory for detailed documentation:
- [Architecture Overview](docs/architecture-overview.md)
- [Implementation Summary](docs/implementation-summary.md)
- [Application Functions Reference](docs/application-functions.mdx)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](docs/contributing.md)
- **Note**: The [Workflow Diagram](docs/workflow-diagram.md) content is now integrated into the [Architecture Overview](docs/architecture-overview.md).

## 🤝 Contributing

1. Follow the TDD workflow defined in `.clinerules`
2. Create feature branches for new work
3. Ensure all tests pass and coverage remains high
4. Use conventional commit messages
5. Submit PRs for review

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [PowerShell App Deployment Toolkit (PSADT)](https://psappdeploytoolkit.com/)
- [MSI Tools](https://github.com/libyal/libmsi) - Cross-platform MSI analysis
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
