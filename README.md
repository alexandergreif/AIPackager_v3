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

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Access the web interface:**
   Open http://localhost:5000 in your browser

## 📋 Features

### ✅ Completed Features

- **Web Interface**: Clean, responsive UI with Tailwind CSS
- **File Upload**: Support for MSI and EXE installer files
- **Metadata Extraction**: Advanced MSI metadata extraction using msitools
- **Workflow Tracking**: Step-by-step progress tracking with CMTrace logging
- **Resume Functionality**: Automatic resumption of interrupted workflows
- **History Management**: View and manage previous package processing jobs
- **PSADT Variables**: Intelligent extraction of PSADT template variables

### 🔄 Workflow Steps

1. **Upload** - Select MSI/EXE installer file
2. **Extract Metadata** - Parse installer metadata using msitools/PE analysis
3. **Preprocess** - Prepare data for AI processing
4. **Generate Prompt** - Create structured prompt for AI
5. **Call AI** - Generate PSADT script using GPT-4o
6. **Render Script** - Finalize and format the output script
7. **Completed** - Download or copy the generated script

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
- **status**: Current processing status
- **current_step**: Current workflow step
- **progress_pct**: Completion percentage
- **upload_time**: Timestamp of upload
- **custom_instructions**: User-provided notes

### Metadata Model
- **package_id**: Foreign key to Package
- **product_name**: Extracted product name
- **version**: Product version
- **publisher**: Software publisher/manufacturer
- **architecture**: Target architecture (x86/x64/arm64)
- **product_code**: MSI Product Code GUID
- **language**: Installation language

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
- 🔄 **Sprint 3**: Template & Prompt Engineering (planned)
- 🔄 **Sprint 4**: AI Integration with GPT-4o (planned)
- 🔄 **Sprint 5**: Polish & Production Features (planned)

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
- [Workflow Diagram](docs/workflow-diagram.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](docs/contributing.md)

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
