"""
Logger factory for creating appropriate logger instances based on configuration.

This module provides a factory function that creates the right type of logger
(console, file, both, or cloud) based on environment configuration.
"""

from typing import Any, List

from app.config import LoggingConfig
from app.logging.logger_protocol import LoggerProtocol
from app.logging.console_logger import ConsoleLogger
from app.logging.file_logger import FileLogger
from app.logging.cloud_logger import CloudLogger


class MultiLogger:
    """Composite logger that writes to multiple backends simultaneously.
    
    This logger allows writing to multiple destinations (e.g., both console
    and file) at the same time. Useful for production where you want logs
    in files but also want to see them in container logs.
    """
    
    def __init__(self, loggers: List[LoggerProtocol]):
        """Initialize the multi-logger.
        
        Args:
            loggers: List of logger instances to write to
        """
        self.loggers = loggers
    
    def debug(self, message: str, **context: Any) -> None:
        """Log to all loggers at debug level."""
        for logger in self.loggers:
            logger.debug(message, **context)
    
    def info(self, message: str, **context: Any) -> None:
        """Log to all loggers at info level."""
        for logger in self.loggers:
            logger.info(message, **context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Log to all loggers at warning level."""
        for logger in self.loggers:
            logger.warning(message, **context)
    
    def error(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log to all loggers at error level."""
        for logger in self.loggers:
            logger.error(message, exc_info=exc_info, **context)
    
    def critical(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log to all loggers at critical level."""
        for logger in self.loggers:
            logger.critical(message, exc_info=exc_info, **context)


# Logger cache to avoid creating duplicate loggers
_logger_cache: dict[str, LoggerProtocol] = {}


def get_logger(name: str) -> LoggerProtocol:
    """Create or retrieve a logger instance based on configuration.
    
    This is the main entry point for obtaining a logger. It creates the
    appropriate logger type (console, file, both, or cloud) based on the
    LOG_TYPE environment variable.
    
    Logger instances are cached to avoid creating duplicates for the same name.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Logger instance following LoggerProtocol
        
    Configuration:
        Set LOG_TYPE environment variable to:
        - "console": Output to stdout/stderr (good for development)
        - "file": Output to rotating log files (good for production)
        - "both": Output to both console and file (good for debugging)
        - "cloud": Output to cloud service (requires implementation)
        
    Example:
        ```python
        from app.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Application started", version="1.0.0")
        ```
    """
    # Return cached logger if it exists
    if name in _logger_cache:
        return _logger_cache[name]
    
    # Create new logger based on configuration
    log_type = LoggingConfig.LOG_TYPE.lower()
    
    if log_type == "console":
        logger = ConsoleLogger(name)
    elif log_type == "file":
        logger = FileLogger(name)
    elif log_type == "both":
        # Create multi-logger with both console and file
        logger = MultiLogger([
            ConsoleLogger(name),
            FileLogger(name)
        ])
    elif log_type == "cloud":
        logger = CloudLogger(name)
    else:
        # Default to console if invalid type specified
        logger = ConsoleLogger(name)
    
    # Cache and return
    _logger_cache[name] = logger
    return logger


def clear_logger_cache() -> None:
    """Clear the logger cache.
    
    Useful for testing or when configuration changes at runtime.
    Note: Typically not needed in production.
    """
    global _logger_cache
    _logger_cache.clear()
