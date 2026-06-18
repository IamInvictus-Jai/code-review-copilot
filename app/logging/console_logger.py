"""
Console logger implementation for development and local debugging.

This logger outputs to stdout/stderr with optional colored output for
better readability during development.
"""

import logging
import sys
from typing import Any

from app.config import LoggingConfig
from app.logging.formatters import JsonFormatter, TextFormatter


class ConsoleLogger:
    """Console logger implementation following LoggerProtocol.
    
    Outputs logs to console (stdout/stderr) with either JSON or text formatting
    based on configuration. Supports colored output for better readability.
    
    This logger is ideal for:
    - Local development
    - Debugging
    - Docker container logs
    - CI/CD pipelines
    """
    
    def __init__(self, name: str):
        """Initialize the console logger.
        
        Args:
            name: Logger name (typically __name__ from calling module)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LoggingConfig.get_log_level_int())
        
        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Set up the console handler with appropriate formatter."""
        # Create console handler (stdout)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(LoggingConfig.get_log_level_int())
        
        # Choose formatter based on configuration
        if LoggingConfig.LOG_FORMAT == "json":
            formatter = JsonFormatter()
        else:
            # Use colored text format for console
            formatter = TextFormatter(use_colors=True)
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def debug(self, message: str, **context: Any) -> None:
        """Log a debug-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
        """
        self.logger.debug(message, extra=context)
    
    def info(self, message: str, **context: Any) -> None:
        """Log an info-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
        """
        self.logger.info(message, extra=context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Log a warning-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
        """
        self.logger.warning(message, extra=context)
    
    def error(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log an error-level message with optional exception info and context.
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
        """
        self.logger.error(message, exc_info=exc_info, extra=context)
    
    def critical(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log a critical-level message with optional exception info and context.
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
        """
        self.logger.critical(message, exc_info=exc_info, extra=context)
