# Workflow Diagram

This document describes the AIPackager v3 workflow process and architecture.

## 🔄 Processing Workflow

```mermaid
graph TD
    A[User Uploads MSI/EXE] --> B[File Validation]
    B --> C[Save to Instance Directory]
    C --> D[Create Package Record]
    D --> E[Extract Metadata]

    E --> F{MSI Tools Available?}
    F -->|Yes| G[Use msiinfo for MSI]
    F -->|No| H[Use Alternative Methods]
    G --> I[Parse Summary Info]
    I --> J[Parse Property Table]
    J --> K[Extract Architecture from Template]
    H --> L[Try LessMSI/PE Analysis]
    L --> K
    K --> M[Generate PSADT Variables]

    M --> N[Preprocess Data]
    N --> O[Generate AI Prompt]
    O --> P[Call GPT-4o API]
    P --> Q[Render PSADT Script]
    Q --> R[Mark as Completed]

    R --> S[Display Results]
    S --> T[Download/Copy Script]

    %% Error Handling
    E --> U{Error?}
    N --> U
    O --> U
    P --> U
    Q --> U
    U -->|Yes| V[Mark as Failed]
    U -->|No| W[Continue]

    %% Resume Logic
    X[App Startup] --> Y[Check Pending Jobs]
    Y --> Z{Found Pending?}
    Z -->|Yes| AA[Resume from Current Step]
    Z -->|No| BB[Ready for New Jobs]
    AA --> N

    style A fill:#e1f5fe
    style R fill:#c8e6c9
    style V fill:#ffcdd2
    style X fill:#fff3e0
```

## 📊 Workflow Steps Enum

```python
class WorkflowStep(enum.Enum):
    UPLOAD = "upload"                    # File uploaded and validated
    EXTRACT_METADATA = "extract_metadata"  # Parsing MSI/EXE metadata
    PREPROCESS = "preprocess"            # Preparing data for AI
    GENERATE_PROMPT = "generate_prompt"  # Creating structured prompt
    CALL_AI = "call_ai"                 # Calling GPT-4o API
    RENDER_SCRIPT = "render_script"     # Finalizing PSADT script
    COMPLETED = "completed"             # Successfully finished
    FAILED = "failed"                   # Error occurred
```

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Web Layer"
        A[Flask Routes] --> B[Jinja2 Templates]
        A --> C[Static Assets]
    end

    subgraph "Business Logic"
        D[PackageRequest] --> E[WorkflowStep Enum]
        D --> F[Metadata Extractor]
        D --> G[File Persistence]
    end

    subgraph "Data Layer"
        H[SQLAlchemy Models] --> I[SQLite Database]
        J[Alembic Migrations] --> I
    end

    subgraph "External Tools"
        K[msitools/msiinfo] --> F
        L[LessMSI] --> F
        M[PE Analysis] --> F
    end

    subgraph "Logging & Monitoring"
        N[CMTrace Logger] --> O[packages.log]
        P[Progress Tracking] --> N
    end

    A --> D
    D --> H
    F --> K
    F --> L
    F --> M
    D --> N

    style A fill:#e3f2fd
    style D fill:#f3e5f5
    style H fill:#e8f5e8
    style K fill:#fff8e1
    style N fill:#fce4ec
```

## 🔄 Resume Functionality

```mermaid
sequenceDiagram
    participant App as Flask App
    participant DB as Database
    participant WF as Workflow
    participant PK as Package

    Note over App: Application Startup
    App->>WF: resume_pending_jobs()
    WF->>DB: Query packages WHERE status NOT IN ('completed', 'failed')
    DB-->>WF: Return pending packages

    loop For each pending package
        WF->>PK: Create PackageRequest(package)
        PK->>PK: resume()
        PK->>PK: Continue from current_step
        PK->>DB: Update status to 'completed'
    end

    WF-->>App: Resume complete

    Note over App: Ready for new requests
```

## 📁 File Processing Flow

```mermaid
graph LR
    A[Upload Form] --> B[File Validation]
    B --> C{Valid MSI/EXE?}
    C -->|No| D[Show Error]
    C -->|Yes| E[Generate UUID]
    E --> F[Save to instance/uploads/]
    F --> G[Create Package Record]
    G --> H[Start Workflow]

    H --> I[Extract Metadata]
    I --> J{MSI File?}
    J -->|Yes| K[Use msitools]
    J -->|No| L[PE Header Analysis]

    K --> M[Summary Info]
    M --> N[Property Table]
    N --> O[Template Parsing]
    O --> P[PSADT Variables]

    L --> Q[Version Info]
    Q --> R[Architecture Detection]
    R --> P

    P --> S[Store in Database]
    S --> T[Continue Workflow]

    style C fill:#fff3e0
    style J fill:#fff3e0
    style P fill:#e8f5e8
```

## 🎯 PSADT Variable Mapping

| Source | PSADT Variable | Fallback Strategy |
|--------|----------------|-------------------|
| Property.ProductName | `appName` | summary_subject → summary_title |
| Property.ProductVersion | `appVersion` | PE version info |
| Property.Manufacturer | `appVendor` | summary_author |
| Property.ProductCode | `productCode` | N/A (MSI only) |
| Template field | `architecture` | PE machine type |
| Property.ProductLanguage | `language` | Template language codes |

## 🔍 Metadata Extraction Strategy

### MSI Files (Preferred: msitools)
1. **Summary Information** (`msiinfo suminfo`)
   - Title, Subject, Author
   - Template (architecture + language)

2. **Property Table** (`msiinfo export Property`)
   - ProductName, ProductVersion
   - Manufacturer, ProductCode
   - UpgradeCode, ProductLanguage

3. **Fallback Methods**
   - LessMSI (if available)
   - Direct MSI database queries

### EXE Files
1. **PE Header Analysis**
   - Machine type (architecture)
   - Timestamp, characteristics

2. **Version Information Resources**
   - ProductName, ProductVersion
   - CompanyName, FileDescription

3. **Platform-Specific**
   - Windows: win32api (if available)
   - Cross-platform: Basic PE parsing

## 📈 Progress Tracking

Progress is tracked at multiple levels:

1. **Package Level**: Overall completion percentage (0-100%)
2. **Step Level**: Current workflow step enum
3. **Logging**: CMTrace format for monitoring
4. **Database**: Persistent state for resume functionality

Each step transition is logged with:
- Timestamp
- Package ID
- Step transition (old → new)
- Success/failure status
