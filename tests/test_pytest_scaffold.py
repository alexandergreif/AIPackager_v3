"""Test pytest scaffold setup."""

from pathlib import Path


def test_tests_directory_exists():
    """Test that tests directory exists and is properly structured."""
    root_path = Path(__file__).parent.parent
    tests_dir = root_path / "tests"
    assert tests_dir.exists(), "tests/ directory should exist"
    assert tests_dir.is_dir(), "tests/ should be a directory"


def test_pytest_can_discover_tests():
    """Test that pytest can discover and run tests."""
    root_path = Path(__file__).parent.parent

    # Check that we have test files that pytest can discover
    test_files = list((root_path / "tests").glob("test_*.py"))
    assert len(test_files) > 0, "Should have test files for pytest to discover"

    # Check that test files contain test functions
    test_functions_found = False
    for test_file in test_files:
        content = test_file.read_text()
        if "def test_" in content:
            test_functions_found = True
            break

    assert test_functions_found, "Should have test functions for pytest to run"


def test_pytest_scaffold_structure():
    """Test that pytest scaffold meets SP0-05 acceptance criteria."""
    root_path = Path(__file__).parent.parent
    tests_dir = root_path / "tests"

    # Verify tests directory structure
    assert tests_dir.exists(), "tests/ directory should exist"
    assert tests_dir.is_dir(), "tests/ should be a directory"

    # Verify we have test files
    test_files = list(tests_dir.glob("test_*.py"))
    assert len(test_files) >= 4, "Should have multiple test files in scaffold"

    # This test itself proves pytest can run and exit 0
    assert True, "If this test runs, pytest scaffold is working"
