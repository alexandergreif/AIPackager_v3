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
**Process File Upload**
- **Description**: Handle file upload and start processing
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: MSI or EXE installer file (required)
  - `custom_instructions`: User notes (optional)
- **Validation**:
  - File extension must be `.msi` or `.exe`
  - File size limit enforced
- **Response**: Redirect to progress page or error flash message

### Package Management

#### `GET /progress/<package_id>`
**Progress Tracking**
- **Description**: Real-time progress monitoring
- **Parameters**:
  - `package_id`: UUID of the package
- **Template**: `progress.html`
- **Response**: HTML page with progress bar and current step

#### `GET /detail/<package_id>`
**Package Details**
- **Description**: Comprehensive package information
- **Parameters**:
  - `package_id`: UUID of the package
- **Template**: `detail.html`
- **Response**: HTML page with metadata table and script preview
- **Features**:
  - Copy to clipboard functionality
  - Download script button
  - Full metadata display

#### `GET /history`
**Package History**
- **Description**: List of all processed packages
- **Template**: `history.html`
- **Response**: HTML table with last 90 days of packages
- **Columns**: Date, Name, Version, Status
- **Interaction**: Click row to view details

### API Endpoints (JSON)

#### `GET /api/packages`
**List All Packages**
- **Description**: JSON list of all packages
- **Response Format**:
```json
[
  {
    "id": "uuid",
    "filename": "installer.msi",
    "status": "completed",
    "upload_time": "2025-01-23T10:30:00Z",
    "progress_pct": 100,
    "current_step": "completed"
  }
]
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

### PackageRequest

```python
class PackageRequest:
    def __init__(self, package: Package) -> None
    def start(self) -> None
    def set_step(self, step_name: str) -> None
    def save_metadata(self, metadata: Dict[str, Any]) -> None
    def resume(self) -> None

    @classmethod
    def resume_pending_jobs(cls) -> None
```

**Methods**:
- `start()`: Initialize processing workflow
- `set_step()`: Update current workflow step with logging
- `save_metadata()`: Store extracted metadata
- `resume()`: Continue processing from current step
- `resume_pending_jobs()`: Class method to resume all pending jobs

### MetadataExtractor

```python
class MetadataExtractor:
    def extract_metadata(self, file_path: str) -> Dict[str, Any]
    def get_psadt_variables(self, metadata: Dict[str, Any]) -> Dict[str, str]

    # Private methods
    def _extract_msi_metadata(self, file_path: str) -> Dict[str, Any]
    def _extract_exe_metadata(self, file_path: str) -> Dict[str, Any]
    def _extract_with_msitools(self, file_path: str) -> Dict[str, Any]
    def _extract_pe_metadata(self, file_path: str) -> Dict[str, Any]
```

**Key Methods**:
- `extract_metadata()`: Main extraction entry point
- `get_psadt_variables()`: Map metadata to PSADT template variables
- `_extract_with_msitools()`: Use msiinfo for MSI analysis
- `_extract_pe_metadata()`: Parse PE headers for EXE files

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
