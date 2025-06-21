"""Test GitHub Actions CI configuration setup."""

import yaml
from pathlib import Path


def test_github_actions_workflow_exists():
    """Test that GitHub Actions CI workflow file exists."""
    root_path = Path(__file__).parent.parent
    ci_workflow = root_path / ".github" / "workflows" / "ci.yml"
    assert ci_workflow.exists(), "GitHub Actions CI workflow should exist"


def test_ci_workflow_configuration():
    """Test that CI workflow has proper configuration."""
    root_path = Path(__file__).parent.parent
    ci_workflow = root_path / ".github" / "workflows" / "ci.yml"

    if not ci_workflow.exists():
        return  # Skip if file doesn't exist

    with open(ci_workflow, "r") as f:
        workflow = yaml.safe_load(f)

    # Check basic structure
    assert "name" in workflow, "Workflow should have a name"
    # YAML interprets "on" as boolean True, so check for that
    assert True in workflow or "on" in workflow, "Workflow should have triggers"
    assert "jobs" in workflow, "Workflow should have jobs"

    # Check for required jobs
    jobs = workflow["jobs"]
    assert "test" in jobs, "Should have a 'test' job"

    # Check test job configuration
    test_job = jobs["test"]
    assert "strategy" in test_job, "Test job should have matrix strategy"
    assert "matrix" in test_job["strategy"], "Should have matrix configuration"

    # Check Python versions
    matrix = test_job["strategy"]["matrix"]
    assert "python-version" in matrix, "Should test multiple Python versions"
    python_versions = matrix["python-version"]
    expected_versions = ["3.10", "3.11", "3.12"]
    for version in expected_versions:
        assert version in python_versions, f"Should test Python {version}"

    # Check for caching
    steps = test_job["steps"]
    cache_steps = [step for step in steps if step.get("name", "").startswith("Cache")]
    assert len(cache_steps) > 0, "Should have caching configured"

    # Check for required tools
    step_commands = []
    for step in steps:
        if "run" in step:
            step_commands.extend(step["run"].split("\n"))

    commands_text = " ".join(step_commands)
    assert "ruff" in commands_text, "Should run Ruff"
    assert "mypy" in commands_text, "Should run MyPy"
    assert "pytest" in commands_text, "Should run pytest"


def test_ci_requirements_satisfied():
    """Test that CI requirements from .clinerules are met."""
    root_path = Path(__file__).parent.parent
    ci_workflow = root_path / ".github" / "workflows" / "ci.yml"

    if not ci_workflow.exists():
        return  # Skip if file doesn't exist

    content = ci_workflow.read_text()

    # Check for required tools mentioned in .clinerules
    assert "ruff" in content, "CI should include Ruff"
    assert "mypy" in content, "CI should include MyPy"
    assert "pytest" in content, "CI should include pytest"

    # Check for caching (performance requirement)
    assert "cache" in content.lower(), "CI should have caching for performance"
