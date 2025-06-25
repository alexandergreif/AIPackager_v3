# Contributing Guidelines

Welcome to AIPackager v3! This document provides guidelines for contributing to the project.

## 🎯 Development Philosophy

### KISS Principle
**Keep It Simple, Stupid** - We prioritize simplicity and clarity over complexity. Every feature should solve a real problem without introducing unnecessary abstraction.

### Test-Driven Development (TDD)
1. **Write failing tests first** that express the acceptance criteria
2. **Implement minimal code** to make tests pass
3. **Refactor** while keeping tests green
4. **Commit** only when all tests pass

### Code Quality Standards
- **Readability**: Code should be self-documenting
- **Consistency**: Follow established patterns
- **Maintainability**: Avoid unnecessary complexity
- **Performance**: Optimize only when needed

## 🔄 Workflow Process

### 1. Branch Strategy

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b sprint/X-Y-feature-name

# Work on your feature
# Commit changes
# Push and create PR

# After merge, clean up
git checkout main
git pull origin main
git branch -d sprint/X-Y-feature-name
```

**Branch Naming Convention**:
- `sprint/X-Y-feature-name` - Sprint tickets
- `hotfix/issue-description` - Critical fixes
- `docs/update-description` - Documentation updates

### 2. Commit Process

```bash
# Stage changes
git add .

# Pre-commit hooks will run automatically:
# - ruff --fix (linting)
# - black (formatting)
# - mypy (type checking)

# Commit with conventional message
git commit -m "SP2-5-XX: Brief description

Detailed explanation of changes:
- What was changed
- Why it was changed
- How it was tested

Acceptance criteria met:
✅ Criterion 1
✅ Criterion 2"
```

### 3. Pull Request Process

1. **Create PR** with descriptive title and body
2. **Link to sprint ticket** or issue
3. **Wait for CI** to pass (ruff, mypy, pytest)
4. **Request review** from team members
5. **Address feedback** and update PR
6. **Merge** only after approval and green CI

## 📝 Coding Standards

### Python Style Guide

#### Type Annotations
```python
# Always use type annotations
def process_package(package_id: str) -> Optional[Package]:
    """Process a package by ID."""
    return get_package(package_id)

# Use proper imports
from typing import Dict, List, Optional, Any
from pathlib import Path
```

#### Error Handling
```python
# Specific exception handling
try:
    metadata = extract_metadata(file_path)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    return None
except MetadataExtractionError as e:
    logger.warning(f"Metadata extraction failed: {e}")
    return {}
```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Something unexpected happened")
logger.error("Error occurred")
logger.critical("Critical error")
```

#### Documentation
```python
def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from installer file.

    Args:
        file_path: Path to the installer file

    Returns:
        Dictionary containing extracted metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        MetadataExtractionError: If extraction fails
    """
```

### Database Patterns

#### Model Definitions
```python
class Package(Base):
    """Package model with proper relationships."""
    __tablename__ = "packages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Use proper relationships
    metadata: Mapped[Optional["Metadata"]] = relationship(
        "Metadata", back_populates="package", cascade="all, delete-orphan"
    )
```

#### Database Operations
```python
def get_package(package_id: str) -> Optional[Package]:
    """Get package with proper session handling."""
    db_service = get_database_service()
    session = db_service.get_session()

    try:
        uuid_obj = UUID(package_id)
        package = session.query(Package).filter(Package.id == uuid_obj).first()
        if package:
            # Ensure relationships are loaded
            _ = package.metadata
        return package
    except ValueError:
        return None
    finally:
        session.close()
```

### Frontend Standards

#### HTML Templates
```html
<!-- Use semantic HTML -->
<main class="container mx-auto px-4">
    <section class="upload-section">
        <h1 class="text-2xl font-bold mb-4">Upload Installer</h1>

        <!-- Accessible forms -->
        <form method="POST" enctype="multipart/form-data">
            <label for="file" class="block text-sm font-medium">
                Select File
            </label>
            <input
                type="file"
                id="file"
                name="file"
                accept=".msi,.exe"
                required
                class="mt-1 block w-full"
            >
        </form>
    </section>
</main>
```

#### JavaScript
```javascript
// Use modern JavaScript
const uploadFile = async (formData) => {
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Upload failed:', error);
        throw error;
    }
};
```

## 🧪 Testing Guidelines

### Test Structure

```python
"""Test module with clear organization."""

import pytest
from src.app import create_app
from src.app.models import Package


class TestPackageModel:
    """Test package model functionality."""

    def test_package_creation(self):
        """Test basic package creation."""
        package = Package(
            filename="test.msi",
            file_path="/path/to/test.msi"
        )

        assert package.filename == "test.msi"
        assert package.status == "uploading"
        assert package.progress_pct == 0

    def test_package_status_transition(self):
        """Test package status changes."""
        package = Package(filename="test.msi", file_path="/path")

        # Test status progression
        package.status = "processing"
        assert package.status == "processing"

        package.status = "completed"
        assert package.status == "completed"
```

### Test Categories

#### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1 second each)

```python
def test_metadata_extraction_unit(mocker):
    """Unit test with mocked dependencies."""
    mock_subprocess = mocker.patch('subprocess.run')
    mock_subprocess.return_value.stdout = "ProductName\tTest App"

    extractor = MetadataExtractor()
    result = extractor._parse_property_table("mock content")

    assert result["ProductName"] == "Test App"
```

#### Integration Tests
- Test component interactions
- Use test database
- Moderate execution time

```python
def test_package_workflow_integration(tmp_path):
    """Integration test for package processing."""
    db_path = tmp_path / "test.db"
    app = create_app({"DATABASE_URL": f"sqlite:///{db_path}"})

    with app.app_context():
        # Test full workflow
        package = create_package("test.msi", "/path/to/test.msi")
        request = PackageRequest(package)
        request.start()

        assert package.status == "processing"
```

#### End-to-End Tests
- Test complete user workflows
- Use real browser (Selenium)
- Slower execution

```python
def test_upload_workflow_e2e(selenium_driver):
    """End-to-end test of upload workflow."""
    driver = selenium_driver
    driver.get("http://localhost:5000")

    # Test upload process
    upload_input = driver.find_element(By.ID, "file")
    upload_input.send_keys("/path/to/test.msi")

    submit_button = driver.find_element(By.TYPE, "submit")
    submit_button.click()

    # Verify redirect to progress page
    assert "/progress/" in driver.current_url
```

### Test Data Management

```python
# conftest.py
@pytest.fixture
def test_package():
    """Create test package."""
    return Package(
        filename="test.msi",
        file_path="/tmp/test.msi",
        status="uploading"
    )

@pytest.fixture
def test_metadata():
    """Create test metadata."""
    return {
        "product_name": "Test Application",
        "version": "1.0.0",
        "publisher": "Test Company",
        "architecture": "x64"
    }
```

## 📋 Sprint Workflow

### Sprint Planning
1. **Review sprint board** (e.g., `sprint2-5.md`)
2. **Pick next ticket** in priority order
3. **Understand acceptance criteria**
4. **Estimate effort** (1-2 commits per ticket)

### Ticket Implementation
1. **Create branch**: `sprint/X-Y-ticket-name`
2. **Write failing tests** that express acceptance criteria
3. **Implement minimal code** to pass tests
4. **Commit with detailed message**
5. **Mark ticket as done** in sprint file

### Example Ticket Flow

```bash
# SP2-5-XX: Add metadata validation
git checkout -b sprint/2-5-xx-metadata-validation

# Write test first
cat > tests/test_metadata_validation.py << EOF
def test_metadata_validation():
    """Test metadata validation logic."""
    validator = MetadataValidator()

    # Test valid metadata
    valid_data = {"product_name": "Test", "version": "1.0"}
    assert validator.validate(valid_data) == True

    # Test invalid metadata
    invalid_data = {"product_name": "", "version": None}
    assert validator.validate(invalid_data) == False
EOF

# Run test (should fail)
python -m pytest tests/test_metadata_validation.py

# Implement feature
# ... write code ...

# Run test (should pass)
python -m pytest tests/test_metadata_validation.py

# Commit
git add .
git commit -m "SP2-5-XX: Add metadata validation

Implemented MetadataValidator class with validation logic:
- Validates required fields are present
- Checks field types and formats
- Returns boolean result

Acceptance criteria met:
✅ Validates product_name is non-empty string
✅ Validates version follows semantic versioning
✅ Returns appropriate error messages"

# Update sprint file
# Mark ticket as ✅ DONE in sprint2-5.md

# Push and create PR
git push origin sprint/2-5-xx-metadata-validation
```

## 🔍 Code Review Guidelines

### For Authors
- **Self-review** before requesting review
- **Write clear PR description** with context
- **Include screenshots** for UI changes
- **Link to relevant tickets** or issues
- **Ensure CI passes** before review request

### For Reviewers
- **Focus on logic and design** over style (tools handle style)
- **Check test coverage** and quality
- **Verify acceptance criteria** are met
- **Suggest improvements** constructively
- **Approve only when confident** in changes

### Review Checklist
- [ ] Code follows project conventions
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated if needed
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

## 🚀 Release Process

### Version Numbering
- **Major**: Breaking changes (v2.0.0 → v3.0.0)
- **Minor**: New features (v3.0.0 → v3.1.0)
- **Patch**: Bug fixes (v3.1.0 → v3.1.1)

### Release Steps
1. **Complete sprint** with all tickets done
2. **Update version** in `pyproject.toml`
3. **Update CHANGELOG.md** with release notes
4. **Create release tag** and GitHub release
5. **Deploy to production** environment

## 🐛 Bug Reports

### Bug Report Template
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g. macOS 12.0]
- Browser: [e.g. Chrome 96]
- Python Version: [e.g. 3.12.2]
- App Version: [e.g. v3.1.0]

## Additional Context
Screenshots, logs, or other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Mockups, examples, or related issues
```

## 📚 Documentation Standards

### Code Documentation
- **Docstrings** for all public functions/classes
- **Type annotations** for all function parameters
- **Inline comments** for complex logic only
- **README updates** for new features

### API Documentation
- **Update API reference** for new endpoints
- **Include request/response examples**
- **Document error conditions**
- **Maintain OpenAPI spec** if applicable

## 🔧 Development Tools

### Required Tools
```bash
# Install development dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Install additional tools
pip install pytest-cov pytest-mock
```

### Recommended IDE Setup

#### VS Code Extensions
- Python
- Pylance
- Black Formatter
- Ruff
- GitLens
- Thunder Client (API testing)

#### PyCharm Configuration
- Enable type checking
- Configure code style (Black)
- Setup run configurations
- Enable pytest integration

## 🤝 Community Guidelines

### Code of Conduct
- **Be respectful** and inclusive
- **Provide constructive feedback**
- **Help others learn** and grow
- **Focus on the code**, not the person
- **Assume positive intent**

### Communication
- **Use clear, concise language**
- **Provide context** for decisions
- **Ask questions** when unclear
- **Share knowledge** and learnings
- **Celebrate successes** together

## 📞 Getting Help

### Resources
- **Documentation**: Check `docs/` directory first
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Ask for help in PR comments

### Contact
- **Project Maintainers**: @username1, @username2
- **Technical Questions**: Create GitHub issue
- **Security Issues**: Email security@project.com
