import logging
import sys
from datetime import datetime
from pathlib import Path
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import config

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[0;36m',  # Cyan
        'INFO': '\033[0;32m',   # Green
        'WARNING': '\033[0;33m', # Yellow
        'ERROR': '\033[0;31m',   # Red
        'CRITICAL': '\033[0;35m' # Purple
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to log level if it's a terminal
        if sys.stderr.isatty():  # Check if output is to a terminal
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Add thread name for async operations
        record.thread_name = f"[{record.threadName}]" if record.threadName != "MainThread" else ""
        
        return super().format(record)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger (usually __name__)
        log_file: Optional specific log file name
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Skip if logger is already configured
    if logger.hasHandlers():
        return logger
    
    # Set global log level (default to INFO)
    logger.setLevel(logging.INFO)
    
    # Create formatters
    console_formatter = CustomFormatter(
        '%(asctime)s %(levelname)s %(thread_name)s [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(threadName)s [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file is None:
        log_file = f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    file_handler = logging.FileHandler(log_dir / log_file)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
default_logger = get_logger("agenthub")

def log_async_start(logger: logging.Logger, operation: str) -> None:
    """Log the start of an async operation"""
    logger.debug(f"Starting async operation: {operation}")

def log_async_complete(logger: logging.Logger, operation: str) -> None:
    """Log the completion of an async operation"""
    logger.debug(f"Completed async operation: {operation}")

def log_exception(logger: logging.Logger, e: Exception, context: str = "") -> None:
    """Log an exception with context"""
    if context:
        logger.error(f"Error in {context}: {str(e)}", exc_info=True)
    else:
        logger.error(str(e), exc_info=True)
