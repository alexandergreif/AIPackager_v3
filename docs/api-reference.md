# API Reference

This document provides detailed information about the AIPackager v3 API endpoints and data models.

## 🌐 Web Routes

### Home & Navigation

#### `GET /`
**Landing Page**
- **Description**: Project overview and navigation
- **Template**: `index.html`
- **Response**: HTML page with project summary and "Get Started" button

#### `GET /upload`
**Upload Form**
- **Description**: File upload interface
- **Template**: `upload.html`
- **Response**: HTML form for MSI/EXE file upload

#### `POST /upload`
**DEPRECATED - Process File Upload**
- **Description**: This route is no longer used for handling file uploads. All uploads are now processed through `POST /api/packages`.
- **Response**: Redirects to the upload page.

### Package Management

#### `GET /progress/<package_id>`
**Progress Tracking**
- **Description**: Real-time progress monitoring. This page triggers the asynchronous 5-stage script generation pipeline if the package has not yet been processed.
- **Parameters**:
  - `package_id`: UUID of the package
- **Template**: `progress.html`
- **Response**: HTML page that connects to the SSE stream for live updates.

#### `GET /stream-progress/<id>`
**Stream Progress (SSE)**
- **Description**: Streams real-time progress updates using Server-Sent Events (SSE).
- **Parameters**:
  - `id`: UUID of the package
- **Response**: `text/event-stream` with JSON data objects.

#### `GET /detail/<package_id>`
**Package Details**
- **Description**: Displays comprehensive package information, including the rendered script and performance metrics.
- **Parameters**:
  - `package_id`: UUID of the package
- **Template**: `detail.html`
- **Response**: HTML page with metadata, script preview, and display metrics.
- **Features**:
  - **Script Rendering**: Uses `ScriptRenderer` to display the final PSADT script.
  - **Metrics Display**: Shows performance metrics calculated by `MetricsService`.
  - Copy to clipboard functionality
  - Download script button

#### `GET /history`
**Package History**
- **Description**: List of all processed packages
- **Template**: `history.html`
- **Response**: HTML table with last 90 days of packages
- **Columns**: Date, Name, Version, Status
- **Interaction**: Click row to view details

#### `GET /logs/<package_id>`
**View Logs**
- **Description**: Displays detailed logs for a specific package.
- **Parameters**:
  - `package_id`: UUID of the package
- **Template**: `logs.html`
- **Response**: HTML page with package logs.

### API Endpoints (JSON)

#### `POST /api/packages`
**Create Package and Upload File**
- **Description**: Handles file upload and initiates the processing workflow. This is the primary endpoint for creating new packages.
- **Workflow**:
  1. Validates file type and size.
  2. Saves the uploaded file to the instance directory.
  3. Creates a new package record in the database.
  4. Extracts metadata from the installer.
  5. Maps extracted data to PSADT variables.
  6. Stores the metadata in the database.
- **Response**: JSON object with the new package's information.
```json
{
  "package_id": "uuid",
  "filename": "installer.msi",
  "status": "uploading",
  "upload_time": "2025-01-23T10:30:00Z",
  "custom_instructions": "User notes"
}
```

#### `GET /api/packages/<package_id>`
**Get Package Details**
- **Description**: Detailed package information
- **Response Format**:
```json
{
  "id": "uuid",
  "filename": "installer.msi",
  "file_path": "/path/to/file",
  "status": "completed",
  "current_step": "completed",
  "progress_pct": 100,
  "upload_time": "2025-01-23T10:30:00Z",
  "custom_instructions": "User notes",
  "metadata": {
    "product_name": "Application Name",
    "version": "1.0.0",
    "publisher": "Company Name",
    "architecture": "x64",
    "product_code": "{GUID}",
    "language": "en-US"
  }
}
```

#### `GET /api/packages/<package_id>/progress`
**Get Progress Status**
- **Description**: Current processing progress
- **Response Format**:
```json
{
  "package_id": "uuid",
  "status": "processing",
  "current_step": "extract_metadata",
  "progress_pct": 25,
  "step_description": "Extracting metadata from installer file"
}
```

#### `POST /api/packages/<uuid:package_id>/generate`
**Generate Script**
- **Description**: Triggers the 5-stage script generation pipeline for a given package.
- **Response**: JSON object confirming the start of the generation process.

#### `POST /api/render/<package_id>`
**Render Script**
- **Description**: Manually re-renders a PSADT script from provided AI sections.
- **Response**: JSON object with the rendered script.

#### `GET /api/packages/<package_id>/logs`
**Get Package Logs**
- **Description**: Retrieves detailed logs for a specific package in JSON format.
- **Response**: JSON object containing the logs.

#### `GET /api/packages`
**List All Packages**
- **Description**: Retrieves a list of all packages.
- **Response**: JSON array of package objects.

### Knowledge Base Management

#### `POST /api/kb/crawl`
**Crawl and Index a URL**
- **Description**: Triggers the `crawl4ai-rag` MCP server to crawl and index a given URL.
- **Request Body**:
```json
{
  "url": "https://example.com"
}
```
- **Response**: JSON object with the status of the crawl operation.

#### `GET /api/kb/sources`
**Get Available Knowledge Base Sources**
- **Description**: Retrieves a list of all available sources from the `crawl4ai-rag` knowledge base.
- **Response**: JSON array of source objects.

## 🗃️ Data Models

### Package Model

```python
class Package(Base):
    __tablename__ = "packages"

    # Primary key
    id: UUID = mapped_column(primary_key=True, default=uuid4)

    # File information
    filename: str = mapped_column(String(255), nullable=False)
    file_path: str = mapped_column(String(500), nullable=False)

    # Timestamps
    upload_time: datetime = mapped_column(DateTime, default=utc_now)

    # Status tracking
    status: str = mapped_column(Enum(...), default="uploading")
    current_step: str = mapped_column(String(50), default="upload")
    progress_pct: int = mapped_column(Integer, default=0)

    # User input
    custom_instructions: Optional[str] = mapped_column(Text)

    # 5-stage pipeline results
    generated_script: Optional[dict] = mapped_column(JSON)
    hallucination_report: Optional[dict] = mapped_column(JSON)
    corrections_applied: Optional[dict] = mapped_column(JSON)
    pipeline_metadata: Optional[dict] = mapped_column(JSON)

    # Relationship
    package_metadata: Optional["Metadata"] = relationship(...)
```

**Status Values**:
- `uploading`: File is being uploaded
- `processing`: Workflow is running
- `completed`: Successfully finished
- `failed`: Error occurred

### Metadata Model

```python
class Metadata(Base):
    __tablename__ = "metadata"

    # Primary key
    id: UUID = mapped_column(primary_key=True, default=uuid4)

    # Foreign key
    package_id: UUID = mapped_column(ForeignKey("packages.id"))

    # MSI/EXE metadata fields
    product_name: Optional[str] = mapped_column(String(255))
    version: Optional[str] = mapped_column(String(50))
    publisher: Optional[str] = mapped_column(String(255))
    install_date: Optional[str] = mapped_column(String(50))
    uninstall_string: Optional[str] = mapped_column(String(500))
    estimated_size: Optional[int] = mapped_column(Integer)

    # Additional metadata
    product_code: Optional[str] = mapped_column(String(100))
    upgrade_code: Optional[str] = mapped_column(String(100))
    language: Optional[str] = mapped_column(String(50))
    architecture: Optional[str] = mapped_column(String(20))
```

### WorkflowStep Enum

```python
class WorkflowStep(enum.Enum):
    UPLOAD = "upload"
    EXTRACT_METADATA = "extract_metadata"
    PREPROCESS = "preprocess"
    GENERATE_PROMPT = "generate_prompt"
    CALL_AI = "call_ai"
    RENDER_SCRIPT = "render_script"
    COMPLETED = "completed"
    FAILED = "failed"
```

## 🔧 Business Logic Classes

### PSADTGenerator
- **Description**: Orchestrates the 5-stage script generation pipeline.
- **Key Methods**:
  - `generate_script()`: Executes the full pipeline, including instruction processing, RAG, script generation, hallucination detection, and advisor correction.

### ScriptRenderer
- **Description**: Renders the final PSADT script from the generated AI sections.
- **Key Methods**:
  - `render_psadt_script()`: Combines the package data and AI-generated content into a complete script.

### MetricsService
- **Description**: Calculates and provides display metrics for the package details page.
- **Key Methods**:
  - `get_display_metrics()`: Returns key performance indicators and other relevant metrics.

### MetadataExtractor
- **Description**: Extracts metadata from installer files.
- **Key Methods**:
  - `extract_file_metadata()`: Main entry point for metadata extraction.
  - `get_psadt_variables()`: Maps extracted metadata to PSADT template variables.

## 🗄️ Database Service

### DatabaseService

```python
class DatabaseService:
    def __init__(self, database_url: str)
    def get_session(self) -> Session
    def create_tables(self) -> None
```

### Helper Functions

```python
def get_database_service() -> DatabaseService
def create_package(filename: str, file_path: str, custom_instructions: Optional[str] = None) -> Package
def get_package(package_id: str) -> Optional[Package]
def update_package_status(package_id: str, status: str) -> bool
def create_metadata(package_id: str, **metadata_fields: Any) -> Metadata
def get_all_packages() -> list[Package]
```

## 📁 File Management

### File Persistence

```python
def save_uploaded_file(file: FileStorage) -> Tuple[str, str]
def get_upload_path(filename: str) -> str
def ensure_upload_directory() -> Path
```

**File Storage**:
- Location: `instance/uploads/`
- Naming: UUID-based to prevent conflicts
- Validation: Extension and size checks

## 📊 Logging & Monitoring

### CMTrace Logging

```python
def setup_cmtrace_logging(log_file: str = "packages.log") -> None
def log_step_transition(package_id: str, old_step: str, new_step: str) -> None
```

**Log Format**:
```
<![LOG[Message]LOG]!><time="HH:MM:SS.fff+000" date="MM-dd-yyyy" component="Component" context="" type="1" thread="1234" file="">
```

**Log Levels**:
- `1`: Information
- `2`: Warning
- `3`: Error

## 🔒 Error Handling

### Common Error Responses

#### File Upload Errors
- **Invalid file type**: Flash message with supported formats
- **File too large**: Flash message with size limit
- **No file selected**: Flash message prompting file selection

#### Processing Errors
- **Metadata extraction failure**: Package marked as `failed`
- **Database errors**: Logged and graceful degradation
- **Missing dependencies**: Fallback to alternative methods

#### API Error Format
```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": "Additional information"
}
```

## 🧪 Testing Endpoints

### Test Configuration
- Use `DATABASE_URL` environment variable for test database
- Temporary file uploads in test directories
- Mock external dependencies (msitools, etc.)

### Test Utilities
```python
def create_test_app(config: dict) -> Flask
def create_test_package(filename: str, status: str = "uploading") -> Package
def mock_metadata_extraction() -> Dict[str, Any]
