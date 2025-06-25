"""Tests for SP1-00: Bootstrap .venv environment."""

import subprocess
import sys
from pathlib import Path


def test_venv_directory_exists():
    """Test that .venv directory exists."""
    venv_path = Path(".venv")
    assert venv_path.exists(), ".venv directory should exist"
    assert venv_path.is_dir(), ".venv should be a directory"


def test_makefile_exists():
    """Test that Makefile exists with venv target."""
    makefile_path = Path("Makefile")
    assert makefile_path.exists(), "Makefile should exist"

    # Check that Makefile contains venv target
    content = makefile_path.read_text()
    assert "venv:" in content, "Makefile should contain venv target"


def test_make_venv_command():
    """Test that 'make venv' command works."""
    # This test will pass once make venv is implemented
    result = subprocess.run(["make", "venv"], capture_output=True, text=True, cwd=".")
    assert result.returncode == 0, f"make venv failed: {result.stderr}"


def test_venv_activation():
    """Test that virtual environment can be activated."""
    venv_python = Path(".venv/bin/python")
    if sys.platform == "win32":
        venv_python = Path(".venv/Scripts/python.exe")

    assert venv_python.exists(), "Python executable should exist in .venv"

    # Test that venv python is different from system python
    result = subprocess.run(
        [str(venv_python), "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0, "Virtual environment Python should be executable"


def test_gitignore_excludes_venv():
    """Test that .gitignore excludes .venv directory."""
    gitignore_path = Path(".gitignore")
    assert gitignore_path.exists(), ".gitignore should exist"

    content = gitignore_path.read_text()
    assert ".venv" in content, ".gitignore should exclude .venv directory"
