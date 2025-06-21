# AIPackager v3

A web application that generates PowerShell App Deployment Toolkit (PSADT) scripts from Windows installer files using AI.

## Quick Start

### Environment Setup

1. **Create virtual environment:**
   ```bash
   make venv
   ```

2. **Activate virtual environment:**
   ```bash
   # Linux/Mac
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   make install
   ```

### Development

- **Run tests:** `make test`
- **Run linting:** `make lint`
- **Clean up:** `make clean`

## Project Structure

```
AIPackager_v3/
├── src/                    # Application source code
├── tests/                  # Test suites
├── requirements.in         # Direct dependencies
├── requirements.txt        # Locked dependencies (generated)
├── Makefile               # Build automation
└── .clinerules            # Development workflow rules
```

## Development Workflow

This project follows Test-Driven Development (TDD) and KISS principles. See `.clinerules` for detailed workflow conventions.

## Sprint Progress

- ✅ **Sprint 0**: Repository & Tooling
- 🚧 **Sprint 1**: UI Skeleton (in progress)
