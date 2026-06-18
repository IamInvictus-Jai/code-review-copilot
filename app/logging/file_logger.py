"""
File logger implementation with automatic rotation.

This logger outputs to rotating log files, automatically creating new files
when size limits are reached. Ideal for production deployments.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

from app.config import LoggingConfig
from app.logging.formatters import JsonFormatter


class FileLogger:
    """File logger implementation following LoggerProtocol.
    
    Outputs logs to rotating files with JSON formatting for easy parsing by
    log aggregation tools. Automatically creates log directory if it doesn't exist.
    
    Features:
    - Automatic file rotation based on size
    - Configurable backup count
    - JSON formatting for machine parsing
    - Automatic directory creation
    
    This logger is ideal for:
    - Production deployments
    - Long-running services
    - Audit trails
    - Post-mortem debugging
    """
    
    def __init__(self, name: str):
        """Initialize the file logger.
        
        Args:
            name: Logger name (typically __name__ from calling module)
        """
        self.logger = logging.getLogger(f"{name}_file")
        self.logger.setLevel(LoggingConfig.get_log_level_int())
        
        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Set up the rotating file handler with JSON formatter."""
        # Ensure log directory exists
        log_dir = os.path.dirname(LoggingConfig.LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            filename=LoggingConfig.LOG_FILE_PATH,
            maxBytes=LoggingConfig.LOG_FILE_MAX_BYTES,
            backupCount=LoggingConfig.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setLevel(LoggingConfig.get_log_level_int())
        
        # Always use JSON format for file logs (easier to parse)
        formatter = JsonFormatter()
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
