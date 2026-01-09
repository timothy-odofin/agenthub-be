"""
Demo script for structured logging.

Shows JSON and human-readable output formats.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.utils.logger import get_logger, LogFormat, log_with_context, log_performance


def demo_json_logging():
    """Demonstrate JSON logging format."""
    print("\n" + "=" * 60)
    print("JSON LOGGING FORMAT (Production)")
    print("=" * 60 + "\n")
    
    logger = get_logger(
        "json_demo",
        log_format=LogFormat.JSON,
        include_file=False
    )
    
    # Basic log
    logger.info("Application started")
    
    # Log with context
    logger.info(
        "User login successful",
        extra={
            "user_id": "user_123",
            "request_id": "req_abc456",
            "ip_address": "192.168.1.1"
        }
    )
    
    # Log with error
    try:
        raise ValueError("Example error for demo")
    except ValueError as e:
        logger.error(
            "Error processing request",
            extra={"request_id": "req_xyz789"},
            exc_info=True
        )
    
    # Performance log
    log_performance(
        logger,
        "database_query",
        duration_ms=1250.5,
        threshold_ms=1000,
        context={"query": "SELECT * FROM users", "request_id": "req_perf123"}
    )


def demo_human_readable_logging():
    """Demonstrate human-readable logging format."""
    print("\n" + "=" * 60)
    print("HUMAN-READABLE LOGGING FORMAT (Development)")
    print("=" * 60 + "\n")
    
    logger = get_logger(
        "human_demo",
        log_format=LogFormat.HUMAN,
        include_file=False
    )
    
    # Basic logs at different levels
    logger.debug("Debug message: checking configuration")
    logger.info("Application initialized successfully")
    logger.warning("High memory usage detected")
    
    # Log with context
    log_with_context(
        logger,
        "INFO",
        "API request completed",
        context={
            "method": "POST",
            "path": "/api/v1/users",
            "status": 200,
            "duration_ms": 45.2,
            "request_id": "req_demo123"
        }
    )
    
    # Error log
    logger.error("Failed to connect to database", extra={"host": "localhost", "port": 5432})


def demo_auto_format():
    """Demonstrate automatic format selection based on environment."""
    print("\n" + "=" * 60)
    print("AUTO FORMAT DETECTION")
    print("=" * 60 + "\n")
    
    # Show current environment
    env = os.getenv("ENVIRONMENT", "development")
    log_format_env = os.getenv("LOG_FORMAT", "auto")
    
    print(f"ENVIRONMENT: {env}")
    print(f"LOG_FORMAT: {log_format_env}")
    print()
    
    logger = get_logger(
        "auto_demo",
        log_format=LogFormat.AUTO,
        include_file=False
    )
    
    logger.info(
        "Format automatically selected based on environment",
        extra={"env": env}
    )


if __name__ == "__main__":
    print("\n🚀 STRUCTURED LOGGING DEMO 🚀\n")
    
    # Demo JSON format (production)
    demo_json_logging()
    
    # Demo human-readable format (development)
    demo_human_readable_logging()
    
    # Demo auto-detection
    demo_auto_format()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("""
To use in production:
1. Set ENVIRONMENT=production
2. Set LOG_FORMAT=json (or let it auto-detect)
3. Point your log aggregator to ./logs/*.log

Example:
    export ENVIRONMENT=production
    export LOG_FORMAT=json
    python examples/structured_logging_demo.py
    """)
