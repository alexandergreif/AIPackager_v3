"""Tests for CMTrace logging functionality."""

import logging
import tempfile
from pathlib import Path
import re

from src.app.logging_cmtrace import (
    CMTraceFormatter,
    setup_cmtrace_logging,
    get_cmtrace_logger,
    log_info,
    log_warning,
    log_error,
    log_debug,
)


class TestCMTraceFormatter:
    """Test CMTrace formatter functionality."""

    def test_cmtrace_format_basic(self):
        """Test basic CMTrace format output."""
        formatter = CMTraceFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="TestComponent",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Check CMTrace format structure
        assert formatted.startswith("<![LOG[Test message]LOG]!>")
        assert 'component="TestComponent"' in formatted
        assert 'type="1"' in formatted  # Info level
        assert 'file="test.py:42"' in formatted

    def test_cmtrace_format_with_context(self):
        """Test CMTrace format with context."""
        formatter = CMTraceFormatter()

        record = logging.LogRecord(
            name="TestComponent",
            level=logging.WARNING,
            pathname="test.py",
            lineno=42,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.context = "Upload processing"

        formatted = formatter.format(record)

        assert 'context="Upload processing"' in formatted
        assert 'type="2"' in formatted  # Warning level

    def test_cmtrace_format_error_level(self):
        """Test CMTrace format with error level."""
        formatter = CMTraceFormatter()

        record = logging.LogRecord(
            name="TestComponent",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert 'type="3"' in formatted  # Error level

    def test_cmtrace_format_timestamp(self):
        """Test CMTrace timestamp format."""
        formatter = CMTraceFormatter()

        record = logging.LogRecord(
            name="TestComponent",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Check timestamp format: time="HH:MM:SS.fff+000" date="MM-dd-yyyy"
        time_pattern = r'time="\d{2}:\d{2}:\d{2}\.\d{3}\+000"'
        date_pattern = r'date="\d{2}-\d{2}-\d{4}"'

        assert re.search(time_pattern, formatted)
        assert re.search(date_pattern, formatted)


class TestCMTraceLogging:
    """Test CMTrace logging setup and functionality."""

    def test_setup_cmtrace_logging(self):
        """Test setting up CMTrace logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_cmtrace_logging(
                log_file=str(log_file), component="TestComponent", level=logging.INFO
            )

            assert logger.name == "TestComponent"
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 2  # File + console handlers

            # Test logging
            logger.info("Test message")

            # Check log file was created and contains CMTrace format
            assert log_file.exists()
            content = log_file.read_text()
            assert "<![LOG[Test message]LOG]!>" in content
            assert 'component="TestComponent"' in content

    def test_setup_cmtrace_logging_with_instance_dir(self):
        """Test setting up CMTrace logging with instance directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            instance_dir = Path(temp_dir)

            logger = setup_cmtrace_logging(
                component="TestComponent", instance_dir=instance_dir
            )

            # Check that logs directory was created
            logs_dir = instance_dir / "logs"
            assert logs_dir.exists()

            # Check that log file was created
            log_file = logs_dir / "aipackager.log"
            logger.info("Test message")

            assert log_file.exists()
            content = log_file.read_text()
            assert "<![LOG[Test message]LOG]!>" in content

    def test_get_cmtrace_logger(self):
        """Test getting CMTrace logger."""
        logger = get_cmtrace_logger("TestComponent")
        assert logger.name == "TestComponent"

    def test_log_convenience_functions(self):
        """Test convenience logging functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_cmtrace_logging(
                log_file=str(log_file), component="TestComponent"
            )

            # Test convenience functions
            log_info(logger, "Info message", "test context")
            log_warning(logger, "Warning message")
            log_error(logger, "Error message")
            log_debug(logger, "Debug message")

            content = log_file.read_text()

            # Check that messages were logged
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            # Debug might not appear if level is INFO

            # Check context was included
            assert 'context="test context"' in content

    def test_cmtrace_format_validation(self):
        """Test that CMTrace format is valid for CMTrace viewer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_cmtrace_logging(
                log_file=str(log_file), component="AIPackager"
            )

            # Log various types of messages
            logger.info("Application started")
            logger.warning("File upload warning")
            logger.error("Processing failed")

            content = log_file.read_text()
            lines = content.strip().split("\n")

            for line in lines:
                # Each line should match CMTrace format
                assert line.startswith("<![LOG[")
                assert "]LOG]!>" in line
                assert "time=" in line
                assert "date=" in line
                assert "component=" in line
                assert "type=" in line
                assert "thread=" in line
                assert "file=" in line

    def test_multiple_loggers(self):
        """Test multiple CMTrace loggers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file1 = Path(temp_dir) / "component1.log"
            log_file2 = Path(temp_dir) / "component2.log"

            logger1 = setup_cmtrace_logging(
                log_file=str(log_file1), component="Component1"
            )

            logger2 = setup_cmtrace_logging(
                log_file=str(log_file2), component="Component2"
            )

            logger1.info("Message from component 1")
            logger2.info("Message from component 2")

            content1 = log_file1.read_text()
            content2 = log_file2.read_text()

            assert 'component="Component1"' in content1
            assert "Message from component 1" in content1

            assert 'component="Component2"' in content2
            assert "Message from component 2" in content2

    def test_log_levels_mapping(self):
        """Test that Python log levels map correctly to CMTrace types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_cmtrace_logging(
                log_file=str(log_file), component="TestComponent", level=logging.DEBUG
            )

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            content = log_file.read_text()

            # Check type mappings
            # Debug and Info should be type="1"
            debug_lines = [
                line for line in content.split("\n") if "Debug message" in line
            ]
            info_lines = [
                line for line in content.split("\n") if "Info message" in line
            ]
            assert any('type="1"' in line for line in debug_lines)
            assert any('type="1"' in line for line in info_lines)

            # Warning should be type="2"
            warning_lines = [
                line for line in content.split("\n") if "Warning message" in line
            ]
            assert any('type="2"' in line for line in warning_lines)

            # Error and Critical should be type="3"
            error_lines = [
                line for line in content.split("\n") if "Error message" in line
            ]
            critical_lines = [
                line for line in content.split("\n") if "Critical message" in line
            ]
            assert any('type="3"' in line for line in error_lines)
            assert any('type="3"' in line for line in critical_lines)

    def test_unicode_handling(self):
        """Test that CMTrace logging handles Unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_cmtrace_logging(
                log_file=str(log_file), component="TestComponent"
            )

            # Log message with Unicode characters
            unicode_message = "Processing file: café_résumé.msi 🚀"
            logger.info(unicode_message)

            content = log_file.read_text(encoding="utf-8")
            assert unicode_message in content
