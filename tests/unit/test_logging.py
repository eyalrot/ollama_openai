"""
Unit tests for logging utilities.
"""

import json
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.utils.logging import (
    JSONFormatter,
    PrettyJSONFormatter,
    error,
    get_logger,
    info,
    log_with_context,
    request_id_context,
    setup_logging,
)


class TestJSONFormatter:
    """Test the JSON formatter."""

    def test_basic_formatting(self):
        """Test basic JSON log formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
        assert "process" in log_data
        assert "thread" in log_data

    def test_exclude_fields(self):
        """Test excluding specific fields."""
        formatter = JSONFormatter(exclude_fields={"timestamp", "process", "thread"})
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" not in log_data
        assert "process" not in log_data
        assert "thread" not in log_data
        assert "message" in log_data

    def test_exception_formatting(self):
        """Test exception information formatting."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
            func="test_function",
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test error"
        assert isinstance(log_data["exception"]["traceback"], list)
        assert len(log_data["exception"]["traceback"]) > 0

    def test_extra_data(self):
        """Test including extra data in logs."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )
        record.extra_data = {"user_id": "123", "action": "login"}

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["user_id"] == "123"
        assert log_data["action"] == "login"

    def test_request_id_context(self):
        """Test request ID from context variable."""
        formatter = JSONFormatter()
        request_id_context.set("test-request-123")

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["request_id"] == "test-request-123"

        # Clean up
        request_id_context.set(None)  # type: ignore[arg-type]

    def test_configuration_options(self):
        """Test formatter configuration options."""
        formatter = JSONFormatter(
            include_timestamp=False,
            include_location=False,
            include_context=False,
        )

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" not in log_data
        assert "module" not in log_data
        assert "function" not in log_data
        assert "line" not in log_data
        assert "pathname" not in log_data


class TestPrettyJSONFormatter:
    """Test the pretty JSON formatter."""

    def test_pretty_formatting(self):
        """Test pretty JSON formatting."""
        formatter = PrettyJSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        output = formatter.format(record)

        # Should be multi-line
        assert "\n" in output

        # Should be valid JSON
        log_data = json.loads(output)
        assert log_data["message"] == "Test message"


class TestSetupLogging:
    """Test the setup_logging function."""

    def setup_method(self):
        """Clear handlers before each test."""
        root_logger = logging.getLogger()
        # Close any existing file handlers to prevent ResourceWarning
        for handler in root_logger.handlers[:]:
            if hasattr(handler, "close"):
                handler.close()
            root_logger.removeHandler(handler)
        root_logger.handlers = []

    def teardown_method(self):
        """Clean up handlers after each test."""
        root_logger = logging.getLogger()
        # Close any file handlers to prevent ResourceWarning
        for handler in root_logger.handlers[:]:
            if hasattr(handler, "close"):
                handler.close()
            root_logger.removeHandler(handler)
        root_logger.handlers = []

    def test_basic_setup(self):
        """Test basic logging setup."""
        logger = setup_logging("INFO")

        assert logger.name == "ollama_openai_proxy"
        assert logger.level == logging.INFO

        # Should have console handler
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)

    def test_log_level_string(self):
        """Test setting log level with string."""
        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG

        logger = setup_logging("WARNING")
        assert logger.level == logging.WARNING

    def test_log_level_int(self):
        """Test setting log level with int."""
        logger = setup_logging(logging.ERROR)
        assert logger.level == logging.ERROR

    def test_json_formatting(self):
        """Test JSON formatting configuration."""
        setup_logging("INFO", use_json=True)

        # Check formatter type
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_pretty_json_formatting(self):
        """Test pretty JSON formatting configuration."""
        setup_logging("INFO", use_json=True, pretty_json=True)

        # Check formatter type
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, PrettyJSONFormatter)

    def test_text_formatting(self):
        """Test text formatting configuration."""
        setup_logging("INFO", use_json=False)

        # Check formatter type
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)

    def test_file_logging(self):
        """Test file logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging("INFO", log_file=log_file)

            # Should have two handlers
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 2

            # Test logging to file
            logger.info("Test file logging")

            # Check file exists and contains log
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test file logging" in content

    def test_configuration_options(self):
        """Test various configuration options."""
        logger = setup_logging(
            "INFO",
            use_json=True,
            include_timestamp=False,
            include_location=False,
            include_context=False,
        )

        # Log a test message
        logger.info("Test message")

        # Capture the output
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter

        assert isinstance(formatter, JSONFormatter)
        assert not formatter.include_timestamp
        assert not formatter.include_location
        assert not formatter.include_context


class TestLoggerFunctions:
    """Test logger utility functions."""

    def test_get_logger(self):
        """Test get_logger function."""
        logger1 = get_logger()
        assert logger1.name == "ollama_openai_proxy"

        logger2 = get_logger("test")
        assert logger2.name == "ollama_openai_proxy.test"

    def test_log_with_context(self):
        """Test logging with additional context."""
        logger = get_logger("test")

        with patch.object(logger, "log") as mock_log:
            log_with_context(
                logger, logging.INFO, "Test message", user_id="123", action="test"
            )

            mock_log.assert_called_once()
            args = mock_log.call_args
            assert args[0][0] == logging.INFO
            assert args[0][1] == "Test message"
            assert args[1]["extra"]["extra_data"]["user_id"] == "123"
            assert args[1]["extra"]["extra_data"]["action"] == "test"

    def test_convenience_functions(self):
        """Test convenience logging functions."""
        with patch("src.utils.logging.log_with_context") as mock_log:
            info("Info message", key="value")
            mock_log.assert_called_with(
                get_logger(),
                logging.INFO,
                "Info message",
                key="value",
            )

            error("Error message", error_code="E001")
            mock_log.assert_called_with(
                get_logger(),
                logging.ERROR,
                "Error message",
                error_code="E001",
            )


class TestIntegration:
    """Integration tests for logging functionality."""

    def test_end_to_end_logging(self):
        """Test complete logging flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            # Setup logging
            logger = setup_logging(
                "INFO",
                log_file=log_file,
                use_json=True,
            )

            # Set request ID
            request_id_context.set("test-123")

            # Log various messages
            logger.info("Starting process", extra={"extra_data": {"step": 1}})
            logger.warning("Warning message")

            try:
                raise ValueError("Test error")
            except ValueError:
                logger.error("Error occurred", exc_info=True)

            # Read and verify log file
            log_content = log_file.read_text()
            log_lines = log_content.strip().split("\n")

            # Should have at least 4 lines (initial setup + 3 logs)
            assert len(log_lines) >= 4

            # Verify each log entry is valid JSON
            for line in log_lines:
                data = json.loads(line)
                assert "timestamp" in data
                assert "level" in data
                assert "message" in data

            # Check specific entries
            info_log = json.loads(log_lines[-3])
            assert info_log["message"] == "Starting process"
            assert info_log["step"] == 1
            assert info_log["request_id"] == "test-123"

            error_log = json.loads(log_lines[-1])
            assert error_log["message"] == "Error occurred"
            assert "exception" in error_log
            assert error_log["exception"]["type"] == "ValueError"

        # Clean up
        request_id_context.set(None)  # type: ignore[arg-type]
