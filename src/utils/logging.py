"""
Logging configuration and utilities.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_object["request_id"] = record.request_id
        
        if hasattr(record, "extra_data"):
            log_object.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_object)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Configure root logger
    logging.basicConfig(level=level)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    
    # Get logger
    logger = logging.getLogger("ollama_openai_proxy")
    logger.handlers = []
    logger.addHandler(console_handler)
    logger.setLevel(level)
    
    return logger