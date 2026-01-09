"""
JSON Formatter for Structured Logging

Provides JSON-formatted logging for production environments.
Compatible with log aggregation systems like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- AWS CloudWatch
- DataDog
- Grafana Loki
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
import sys


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs logs in JSON format with consistent structure for easy parsing
    by log aggregation systems.
    
    Features:
    - Structured JSON output
    - Automatic field extraction
    - Exception stack traces
    - Custom extra fields support
    - ISO 8601 timestamps
    - Environment context
    """
    
    def __init__(
        self,
        *,
        service_name: str = "agenthub",
        environment: str = "development",
        include_extra: bool = True
    ):
        """
        Initialize JSON formatter.
        
        Args:
            service_name: Name of the service (for distributed systems)
            environment: Environment name (dev, staging, production)
            include_extra: Whether to include extra fields from log records
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra = include_extra
        
        # Fields to exclude from extra (standard logging fields)
        self.excluded_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName',
            'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'taskName', 'thread_name'
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": self._get_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            
            # Source location
            "source": {
                "file": record.pathname,
                "function": record.funcName,
                "line": record.lineno,
                "module": record.module,
            },
            
            # Process/Thread info
            "process": {
                "id": record.process,
                "name": record.processName,
            },
            "thread": {
                "id": record.thread,
                "name": record.threadName,
            }
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self._format_exception(record)
        
        # Add stack trace if present
        if record.stack_info:
            log_data["stack_trace"] = record.stack_info
        
        # Add extra fields (e.g., request_id, user_id, etc.)
        if self.include_extra:
            extra_fields = self._extract_extra_fields(record)
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def _get_timestamp(self, record: logging.LogRecord) -> str:
        """Get ISO 8601 formatted timestamp."""
        dt = datetime.fromtimestamp(record.created)
        return dt.isoformat() + 'Z'
    
    def _format_exception(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format exception information."""
        if not record.exc_info:
            return {}
        
        exc_type, exc_value, exc_tb = record.exc_info
        
        return {
            "type": exc_type.__name__ if exc_type else None,
            "message": str(exc_value),
            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb)
        }
    
    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract custom fields added via extra parameter."""
        extra = {}
        
        for key, value in record.__dict__.items():
            if key not in self.excluded_fields:
                # Skip private attributes
                if not key.startswith('_'):
                    extra[key] = value
        
        return extra


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development/console output.
    
    Provides colored output with clean formatting for local development.
    """
    
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[0;35m', # Purple
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize human-readable formatter.
        
        Args:
            use_colors: Whether to use colors (auto-detected if terminal)
        """
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors and sys.stderr.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and clean layout."""
        # Save original values
        original_levelname = record.levelname
        
        # Add colors if enabled
        if self.use_colors:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
                )
        
        # Format the main message
        formatted = super().format(record)
        
        # Add extra fields if present
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            extras_str = " | ".join(f"{k}={v}" for k, v in extra_fields.items())
            formatted += f"\n  └─ {extras_str}"
        
        # Add exception info if present
        if record.exc_info and not record.exc_text:
            formatted += "\n" + self.formatException(record.exc_info)
        
        # Restore original values
        record.levelname = original_levelname
        
        return formatted
    
    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields for display."""
        excluded = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName',
            'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'taskName', 'thread_name',
            'asctime'
        }
        
        extra = {}
        for key, value in record.__dict__.items():
            if key not in excluded and not key.startswith('_'):
                extra[key] = value
        
        return extra


def format_log_context(context: Dict[str, Any]) -> str:
    """
    Format a context dictionary for logging.
    
    Useful for formatting structured data in a readable way.
    
    Args:
        context: Dictionary of context data
        
    Returns:
        Formatted string
    """
    if not context:
        return ""
    
    items = [f"{k}={v}" for k, v in context.items()]
    return " | ".join(items)
