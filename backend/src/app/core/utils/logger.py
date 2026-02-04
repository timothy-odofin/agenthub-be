"""
Enhanced Logging System

Supports both human-readable (development) and JSON (production) logging formats.
Automatically configures based on environment or explicit settings.

Features:
- JSON logging for production (structured, parseable)
- Colored console logging for development
- File rotation support
- Request ID tracking
- Performance logging
- Exception tracking
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from app.core.utils.formatters import JSONFormatter, HumanReadableFormatter


class LogFormat(str, Enum):
    """Logging format options."""
    JSON = "json"
    HUMAN = "human"
    AUTO = "auto"


# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)


def get_log_format() -> LogFormat:
    """
    Determine the appropriate log format based on environment.
    
    Returns:
        LogFormat: The format to use (JSON for production, HUMAN for development)
    """
    # Check environment variable
    env_format = os.getenv("LOG_FORMAT", "").lower()
    if env_format == "json":
        return LogFormat.JSON
    elif env_format == "human":
        return LogFormat.HUMAN
    
    # Auto-detect based on environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    # Use JSON in production, human-readable otherwise
    if environment in ("production", "prod", "staging"):
        return LogFormat.JSON
    else:
        return LogFormat.HUMAN


def get_logger(
    name: str,
    log_file: Optional[str] = None,
    log_format: LogFormat = LogFormat.AUTO,
    service_name: str = "agenthub",
    include_console: bool = True,
    include_file: bool = True
) -> logging.Logger:
    """
    Get a configured logger instance with structured logging support.
    
    Args:
        name: The name of the logger (usually __name__)
        log_file: Optional specific log file name
        log_format: Log format (JSON, HUMAN, or AUTO-detect)
        service_name: Service name for distributed systems
        include_console: Whether to include console output
        include_file: Whether to include file output
    
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": "123", "request_id": "req_abc"})
        ```
    """
    logger = logging.getLogger(name)
    
    # Skip if logger is already configured
    if logger.hasHandlers():
        return logger
    
    # Set global log level from environment or default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Determine format
    if log_format == LogFormat.AUTO:
        log_format = get_log_format()
    
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Console Handler
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if log_format == LogFormat.JSON:
            console_formatter = JSONFormatter(
                service_name=service_name,
                environment=environment,
                include_extra=True
            )
        else:
            console_formatter = HumanReadableFormatter(use_colors=True)
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File Handler
    if include_file:
        if log_file is None:
            log_file = f"{datetime.now().strftime('%Y-%m-%d')}.log"
        
        file_handler = logging.FileHandler(log_dir / log_file)
        
        # Always use JSON format for files (easier to parse)
        file_formatter = JSONFormatter(
            service_name=service_name,
            environment=environment,
            include_extra=True
        )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
default_logger = get_logger("agenthub")


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    exc_info: bool = False
) -> None:
    """
    Log a message with structured context.
    
    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        context: Additional context as dictionary
        exc_info: Whether to include exception info
        
    Example:
        ```python
        log_with_context(
            logger,
            "INFO",
            "User action completed",
            context={"user_id": "123", "action": "login", "request_id": "req_abc"}
        )
        ```
    """
    log_method = getattr(logger, level.lower())
    if context:
        log_method(message, extra=context, exc_info=exc_info)
    else:
        log_method(message, exc_info=exc_info)


def log_async_start(logger: logging.Logger, operation: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of an async operation.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        context: Additional context
    """
    log_with_context(logger, "DEBUG", f"Starting async operation: {operation}", context)


def log_async_complete(
    logger: logging.Logger,
    operation: str,
    duration_ms: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the completion of an async operation.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration_ms: Operation duration in milliseconds
        context: Additional context
    """
    ctx = context or {}
    if duration_ms is not None:
        ctx["duration_ms"] = duration_ms
    
    log_with_context(logger, "DEBUG", f"Completed async operation: {operation}", ctx)


def log_exception(
    logger: logging.Logger,
    e: Exception,
    context: str = "",
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with context and stack trace.
    
    Args:
        logger: Logger instance
        e: Exception to log
        context: Descriptive context
        extra: Additional context data
    """
    message = f"Error in {context}: {str(e)}" if context else f"Error: {str(e)}"
    log_with_context(logger, "ERROR", message, extra, exc_info=True)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    threshold_ms: float = 1000,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics, warn if above threshold.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration_ms: Operation duration in milliseconds
        threshold_ms: Warning threshold in milliseconds
        context: Additional context
    """
    ctx = context or {}
    ctx["duration_ms"] = duration_ms
    ctx["operation"] = operation
    
    if duration_ms > threshold_ms:
        log_with_context(
            logger,
            "WARNING",
            f"Slow operation: {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)",
            ctx
        )
    else:
        log_with_context(
            logger,
            "DEBUG",
            f"Operation completed: {operation} took {duration_ms:.2f}ms",
            ctx
        )


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log an HTTP request with structured data.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        request_id: Request ID for tracing
        user_id: User ID if authenticated
    """
    context = {
        "http_method": method,
        "http_path": path,
        "http_status": status_code,
        "duration_ms": duration_ms,
    }
    
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    
    level = "WARNING" if status_code >= 400 else "INFO"
    log_with_context(
        logger,
        level,
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
        context
    )

