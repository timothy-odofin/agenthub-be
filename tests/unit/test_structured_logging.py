"""
Unit tests for structured logging (JSON format).

Tests JSON formatter, human-readable formatter, and logger configuration.
"""

import json
import logging
import pytest
import os
from io import StringIO
from datetime import datetime

from app.core.utils.formatters import JSONFormatter, HumanReadableFormatter, format_log_context
from app.core.utils.logger import get_logger, get_log_format, LogFormat, log_with_context


class TestJSONFormatter:
    """Test JSON formatter for structured logging."""

    def test_json_formatter_basic_message(self):
        """JSON formatter should output valid JSON."""
        formatter = JSONFormatter(service_name="test_service", environment="test")
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        # Should be valid JSON
        log_data = json.loads(output)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["service"] == "test_service"
        assert log_data["environment"] == "test"
        assert log_data["logger"] == "test.logger"

    def test_json_formatter_with_extra_fields(self):
        """JSON formatter should include extra fields."""
        formatter = JSONFormatter(service_name="test", environment="test", include_extra=True)
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.request_id = "req_123"
        record.user_id = "user_456"
        record.custom_field = "custom_value"
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "extra" in log_data
        assert log_data["extra"]["request_id"] == "req_123"
        assert log_data["extra"]["user_id"] == "user_456"
        assert log_data["extra"]["custom_field"] == "custom_value"

    def test_json_formatter_with_exception(self):
        """JSON formatter should include exception info."""
        formatter = JSONFormatter(service_name="test", environment="test")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test error"
        assert "traceback" in log_data["exception"]
        assert isinstance(log_data["exception"]["traceback"], list)

    def test_json_formatter_timestamp_format(self):
        """JSON formatter should use ISO 8601 timestamps."""
        formatter = JSONFormatter(service_name="test", environment="test")
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        # Should have timestamp field
        assert "timestamp" in log_data
        
        # Should be valid ISO 8601 format (ends with Z)
        assert log_data["timestamp"].endswith("Z")
        
        # Should be parseable as datetime
        timestamp = log_data["timestamp"].rstrip('Z')
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_json_formatter_source_location(self):
        """JSON formatter should include source code location."""
        formatter = JSONFormatter(service_name="test", environment="test")
        
        record = logging.LogRecord(
            name="my.module",
            level=logging.INFO,
            pathname="/app/src/my/module.py",
            lineno=123,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.module = "module"
        record.funcName = "my_function"
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "source" in log_data
        assert log_data["source"]["file"] == "/app/src/my/module.py"
        assert log_data["source"]["function"] == "my_function"
        assert log_data["source"]["line"] == 123
        assert log_data["source"]["module"] == "module"

    def test_json_formatter_process_thread_info(self):
        """JSON formatter should include process and thread info."""
        formatter = JSONFormatter(service_name="test", environment="test")
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "process" in log_data
        assert "id" in log_data["process"]
        assert "name" in log_data["process"]
        
        assert "thread" in log_data
        assert "id" in log_data["thread"]
        assert "name" in log_data["thread"]

    def test_json_formatter_excludes_internal_fields(self):
        """JSON formatter should exclude internal logging fields from extra."""
        formatter = JSONFormatter(service_name="test", environment="test", include_extra=True)
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        # These should NOT appear in extra
        record.custom_field = "should_appear"
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        # Should have custom field
        assert "extra" in log_data
        assert log_data["extra"]["custom_field"] == "should_appear"
        
        # Should NOT have internal fields in extra
        if "extra" in log_data:
            assert "name" not in log_data["extra"]
            assert "message" not in log_data["extra"]
            assert "levelname" not in log_data["extra"]


class TestHumanReadableFormatter:
    """Test human-readable formatter for console output."""

    def test_human_readable_basic_format(self):
        """Human-readable formatter should produce clean output."""
        formatter = HumanReadableFormatter(use_colors=False)
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        assert "INFO" in output
        assert "test.logger" in output
        assert "42" in output  # line number
        assert "Test message" in output

    def test_human_readable_with_extra_fields(self):
        """Human-readable formatter should display extra fields nicely."""
        formatter = HumanReadableFormatter(use_colors=False)
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        record.request_id = "req_123"
        record.user_id = "user_456"
        
        output = formatter.format(record)
        
        # Extra fields should be displayed
        assert "request_id=req_123" in output
        assert "user_id=user_456" in output


class TestGetLogFormat:
    """Test log format auto-detection."""

    def test_get_log_format_from_env_variable(self, monkeypatch):
        """Should use LOG_FORMAT environment variable if set."""
        monkeypatch.setenv("LOG_FORMAT", "json")
        assert get_log_format() == LogFormat.JSON
        
        monkeypatch.setenv("LOG_FORMAT", "human")
        assert get_log_format() == LogFormat.HUMAN

    def test_get_log_format_auto_production(self, monkeypatch):
        """Should use JSON for production environment."""
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "production")
        assert get_log_format() == LogFormat.JSON

    def test_get_log_format_auto_staging(self, monkeypatch):
        """Should use JSON for staging environment."""
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "staging")
        assert get_log_format() == LogFormat.JSON

    def test_get_log_format_auto_development(self, monkeypatch):
        """Should use HUMAN for development environment."""
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")
        assert get_log_format() == LogFormat.HUMAN


class TestGetLogger:
    """Test logger configuration."""

    def test_get_logger_creates_logger(self):
        """Should create a logger instance."""
        import uuid
        unique_name = f"test_logger_{uuid.uuid4().hex[:8]}"
        
        logger = get_logger(unique_name, include_file=False, include_console=True)
        
        assert logger is not None
        assert logger.name == unique_name
        # Logger is created (handlers may be added after first call)

    def test_get_logger_returns_same_instance(self):
        """Should return the same logger instance for the same name."""
        import uuid
        unique_name = f"test_logger_{uuid.uuid4().hex[:8]}"
        
        logger1 = get_logger(unique_name, include_file=False)
        logger2 = get_logger(unique_name, include_file=False)
        
        assert logger1 is logger2

    def test_json_formatter_can_be_instantiated(self):
        """JSON formatter should be instantiatable."""
        formatter = JSONFormatter(service_name="test", environment="test")
        assert formatter is not None
        assert formatter.service_name == "test"
        assert formatter.environment == "test"

    def test_human_formatter_can_be_instantiated(self):
        """Human-readable formatter should be instantiatable."""
        formatter = HumanReadableFormatter(use_colors=False)
        assert formatter is not None


class TestLogWithContext:
    """Test structured logging with context."""

    def test_log_with_context_includes_extra_fields(self):
        """log_with_context should include extra fields in log record."""
        # Create a logger with a custom handler to capture output
        logger = logging.getLogger("test_context_logger")
        logger.handlers.clear()  # Clear any existing handlers
        
        # Create a handler that captures the log record
        class RecordCapture(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
            
            def emit(self, record):
                self.records.append(record)
        
        capture = RecordCapture()
        logger.addHandler(capture)
        logger.setLevel(logging.INFO)
        
        # Log with context
        context = {"request_id": "req_123", "user_id": "user_456"}
        log_with_context(logger, "INFO", "Test message", context)
        
        # Check that the record has the extra fields
        assert len(capture.records) == 1
        record = capture.records[0]
        assert hasattr(record, "request_id")
        assert record.request_id == "req_123"
        assert hasattr(record, "user_id")
        assert record.user_id == "user_456"


class TestFormatLogContext:
    """Test context formatting helper."""

    def test_format_log_context_creates_readable_string(self):
        """Should format context dictionary as readable string."""
        context = {"request_id": "req_123", "user_id": "user_456", "action": "login"}
        
        result = format_log_context(context)
        
        assert "request_id=req_123" in result
        assert "user_id=user_456" in result
        assert "action=login" in result
        assert "|" in result  # Separator

    def test_format_log_context_empty_dict(self):
        """Should handle empty dictionary."""
        result = format_log_context({})
        assert result == ""

    def test_format_log_context_none(self):
        """Should handle None."""
        result = format_log_context(None)
        assert result == ""
