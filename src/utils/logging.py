"""
Logging configuration and utilities.
"""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Context variable for request ID
request_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(
        self,
        *,
        include_timestamp: bool = True,
        include_location: bool = True,
        include_context: bool = True,
        exclude_fields: Optional[set[str]] = None,
    ):
        """
        Initialize JSON formatter.

        Args:
            include_timestamp: Include timestamp in log output
            include_location: Include module, function, and line info
            include_context: Include context variables like request_id
            exclude_fields: Set of field names to exclude from output
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_location = include_location
        self.include_context = include_context
        self.exclude_fields = exclude_fields or set()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_object: Dict[str, Any] = {}

        # Add timestamp
        if self.include_timestamp and "timestamp" not in self.exclude_fields:
            log_object["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add basic fields
        if "level" not in self.exclude_fields:
            log_object["level"] = record.levelname
        if "logger" not in self.exclude_fields:
            log_object["logger"] = record.name
        if "message" not in self.exclude_fields:
            log_object["message"] = record.getMessage()

        # Add location info
        if self.include_location:
            if "module" not in self.exclude_fields:
                log_object["module"] = record.module
            if "function" not in self.exclude_fields:
                log_object["function"] = record.funcName
            if "line" not in self.exclude_fields:
                log_object["line"] = record.lineno
            if "pathname" not in self.exclude_fields:
                log_object["pathname"] = record.pathname

        # Add context variables
        if self.include_context:
            request_id = request_id_context.get()
            if request_id and "request_id" not in self.exclude_fields:
                log_object["request_id"] = request_id

        # Add any extra fields from the record
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            for key, value in record.extra_data.items():
                if key not in self.exclude_fields:
                    log_object[key] = value

        # Add exception info if present
        if record.exc_info and "exception" not in self.exclude_fields:
            log_object["exception"] = {
                "type": (
                    record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
                ),
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info).split("\n"),
            }

        # Process ID and thread info (useful for debugging)
        if "process" not in self.exclude_fields:
            log_object["process"] = record.process
        if "thread" not in self.exclude_fields:
            log_object["thread"] = record.thread

        return json.dumps(log_object, default=str, ensure_ascii=False)


class PrettyJSONFormatter(JSONFormatter):
    """JSON formatter with pretty printing for development."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as pretty-printed JSON."""
        # Get the base JSON object
        json_str = super().format(record)
        log_object = json.loads(json_str)

        # Pretty print with indentation
        return json.dumps(
            log_object, indent=2, default=str, ensure_ascii=False, sort_keys=False
        )


def setup_logging(
    level: Union[str, int] = "INFO",
    *,
    log_file: Optional[Path] = None,
    use_json: bool = True,
    pretty_json: bool = False,
    include_timestamp: bool = True,
    include_location: bool = True,
    include_context: bool = True,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (string or int)
        log_file: Optional file path for file logging
        use_json: Use JSON formatting (False for plain text)
        pretty_json: Use pretty-printed JSON (only if use_json=True)
        include_timestamp: Include timestamp in logs
        include_location: Include code location info
        include_context: Include context variables

    Returns:
        Configured logger instance
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Clear any existing handlers on root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(level)

    # Create formatter
    formatter: Union[JSONFormatter, PrettyJSONFormatter, logging.Formatter]
    if use_json:
        if pretty_json:
            formatter = PrettyJSONFormatter(
                include_timestamp=include_timestamp,
                include_location=include_location,
                include_context=include_context,
            )
        else:
            formatter = JSONFormatter(
                include_timestamp=include_timestamp,
                include_location=include_location,
                include_context=include_context,
            )
    else:
        # Standard text formatter
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if include_location:
            format_str = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
            )
        formatter = logging.Formatter(format_str)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # Create file handler if requested
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    # Get application logger
    logger = logging.getLogger("ollama_openai_proxy")
    logger.setLevel(level)

    # Log initial setup message
    logger.info(
        "Logging configured",
        extra={
            "extra_data": {
                "log_level": logging.getLevelName(level),
                "json_format": use_json,
                "log_file": str(log_file) if log_file else None,
            }
        },
    )

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to ollama_openai_proxy)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"ollama_openai_proxy.{name}")
    return logging.getLogger("ollama_openai_proxy")


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **kwargs: Any,
) -> None:
    """
    Log a message with additional context.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **kwargs: Additional context fields
    """
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.log(level, message, extra=extra)


# Convenience functions for logging with context
def debug(message: str, **kwargs: Any) -> None:
    """Log debug message with context."""
    log_with_context(get_logger(), logging.DEBUG, message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """Log info message with context."""
    log_with_context(get_logger(), logging.INFO, message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log warning message with context."""
    log_with_context(get_logger(), logging.WARNING, message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log error message with context."""
    log_with_context(get_logger(), logging.ERROR, message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    """Log critical message with context."""
    log_with_context(get_logger(), logging.CRITICAL, message, **kwargs)
