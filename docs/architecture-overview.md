# AIPackager v3 - Architecture Overview

This document provides a high-level overview of the AIPackager v3 system architecture, detailing its core components, their interactions, and the flow of data through the application.

---

## 1. System Overview

AIPackager v3 is a Flask-based web application designed to automate the generation of PowerShell App Deployment Toolkit (PSADT) scripts. It leverages advanced AI capabilities, including a 5-stage self-correcting pipeline and integration with a knowledge base via the Model Context Protocol (MCP), to provide accurate and robust script generation.

The application's primary function is to accept installer file uploads, extract metadata, and then generate a PSADT script based on user instructions and extracted information. The entire process is designed to be asynchronous, providing real-time progress updates to the user.

---

## 2. Core Architectural Layers

The AIPackager v3 architecture is logically divided into several interconnected layers:

### 2.1. Web Layer (Frontend & API)
*   **Purpose**: Handles user interaction, displays application status, and exposes API endpoints for various functionalities.
*   **Components**:
    *   **Flask Routes (`src/app/routes.py`)**: Defines all web routes (e.g., `/`, `/upload`, `/progress/<id>`, `/detail/<id>`, `/history`, `/tools`) and API endpoints (e.g., `/api/packages`, `/api/kb/sources`, `/api/health/mcp`). These routes manage HTTP requests and responses, rendering HTML templates or returning JSON data.
    *   **Enhanced Templates (`src/app/templates/`)**: Jinja2 templates (`.html`) for rendering dynamic web pages, including forms, progress indicators, and detailed package views.
    *   **Pipeline Progress UI**: Integrates with Server-Sent Events (SSE) to provide real-time updates on the script generation pipeline's progress.

### 2.2. 5-Stage AI Pipeline
*   **Purpose**: The central intelligence of the application, responsible for orchestrating the AI-driven PSADT script generation process. This pipeline is self-correcting, ensuring high-quality output.
*   **Components**:
    *   **Pipeline Orchestrator (`src/aipackager/workflow.py`, `src/app/services/script_generator.py`)**: Manages the sequential execution of the five stages, handling state transitions, error recovery, and progress reporting.
    *   **Stage 1: Instruction Processor**: Converts natural language user instructions into structured, actionable commands and predicts necessary PSADT cmdlets.
    *   **Stage 2: Targeted RAG (Retrieval Augmented Generation)**: Queries the knowledge base for relevant documentation based on predicted cmdlets, compiling a focused context for script generation.
    *   **Stage 3: Script Generator**: Generates an initial PowerShell script using the compiled context and applies the standard PSADT template structure.
    *   **Stage 4: Hallucination Detector**: Validates the generated script against the knowledge graph to identify any invalid cmdlets, parameters, or logical inconsistencies (hallucinations).
    *   **Stage 5: Advisor AI**: If hallucinations are detected, this stage queries the RAG system for correction documentation and generates a refined, corrected script, which is then re-validated.

### 2.3. Knowledge & Validation Layer
*   **Purpose**: Provides the necessary data and tools for grounding AI responses, validating generated content, and enhancing the intelligence of the pipeline.
*   **Components**:
    *   **`crawl4ai-rag` MCP Server**: An external Model Context Protocol (MCP) server that acts as the primary interface to the knowledge base. It provides tools for:
        *   **PSADT Documentation**: Stores and retrieves official PSADT cmdlet documentation.
        *   **Knowledge Graph (Neo4j)**: A graph database that stores the structural relationships of code (classes, methods, functions, imports) from various repositories. Used by the Hallucination Detector for semantic validation.
        *   **Vector Database (Supabase)**: Stores embeddings of crawled web content and documentation, enabling efficient RAG queries.
    *   **`MCPService` (`src/app/services/mcp_service.py`)**: The application's internal service responsible for communicating with the `crawl4ai-rag` MCP server, abstracting the complexities of tool calls and resource access.

### 2.4. Data Layer
*   **Purpose**: Manages persistent storage of application data, including package information, metadata, and pipeline states.
*   **Components**:
    *   **Enhanced Models (`src/app/models.py`)**: SQLAlchemy ORM models (`Package`, `Metadata`) defining the database schema. The `Package` model includes fields for tracking pipeline results (generated script, hallucination report, corrections applied, pipeline metadata) and current processing status.
    *   **Database Service (`src/app/database.py`)**: Provides a centralized interface for database session management and common CRUD operations on `Package` and `Metadata` records.
    *   **Pipeline State Tracking**: The `Package` model and associated services (`src/app/progress.py`, `src/app/package_logger.py`) track the current step and progress percentage of each package through the 5-stage pipeline, enabling resume capabilities.
    *   **Alembic Migrations (`alembic/`)**: Manages database schema changes, ensuring that the database structure remains compatible with application updates.

---

## 3. Data Flow and Interactions

1.  **User Upload**: A user uploads an MSI/EXE installer file via the web interface (`/upload` route, handled by `api_create_package`).
2.  **File Persistence**: The uploaded file is securely saved to the instance directory (`src/app/file_persistence.py`).
3.  **Package & Metadata Creation**: A new `Package` record is created in the database, and metadata is extracted from the installer (`src/app/metadata_extractor.py`) and stored as a `Metadata` record, linked to the `Package`.
4.  **Pipeline Initiation**: The 5-stage AI pipeline is triggered (either immediately or on demand via `/progress/<id>` or `/api/packages/<uuid:package_id>/generate`).
5.  **AI Processing**:
    *   The `PSADTGenerator` orchestrates the pipeline stages.
    *   Stages 1, 2, 4, and 5 interact with the `crawl4ai-rag` MCP server via `MCPService` to leverage the knowledge graph and RAG capabilities for instruction processing, documentation retrieval, hallucination detection, and script correction.
    *   Stage 3 generates the initial script, and `ScriptRenderer` combines AI-generated sections into a final PSADT script.
6.  **Progress Monitoring**: Real-time progress updates are pushed to the frontend via Server-Sent Events (`/stream-progress/<id>`).
7.  **Result Storage**: The generated script, hallucination report, and correction details are stored back in the `Package` record in the database.
8.  **Display Results**: The user can view detailed package information, including the rendered script and performance metrics, on the `/detail/<id>` page.
9.  **Health Checks**: Dedicated API endpoints allow for monitoring the health of the MCP server, Neo4j, Supabase, and the Flask application itself, ensuring operational stability.

---

This architectural overview highlights the modular design, the central role of the 5-stage AI pipeline, and the critical integration with external knowledge base services to deliver an intelligent and robust PSADT script generation solution.
