"""
Log formatters for structured and human-readable output.

This module provides two formatter classes:
- JsonFormatter: Structured JSON output for machine parsing
- TextFormatter: Human-readable colored output for development
"""

import logging
from pythonjsonlogger import jsonlogger
from app.config import LoggingConfig
from app.logging.context import get_all_context


class JsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter for structured logging.
    
    Outputs logs as JSON objects with consistent fields for easy parsing
    by log aggregation tools (e.g., CloudWatch, Datadog, ELK stack).
    
    Each log record includes:
    - timestamp: ISO format timestamp
    - level: Log level name (INFO, ERROR, etc.)
    - module: Python module name
    - function: Function name where log was called
    - message: The log message
    - environment: Current environment (dev/prod)
    - Plus any context fields from LoggingContext
    """
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """Add custom fields to the log record.
        
        Args:
            log_record: Dictionary that will be converted to JSON
            record: Python logging.LogRecord object
            message_dict: Additional fields from the log call
        """
        super(JsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['environment'] = LoggingConfig.ENVIRONMENT
        
        # Add context variables from LoggingContext
        context = get_all_context()
        if context:
            log_record.update(context)
        
        # Ensure message is always present
        if 'message' not in log_record:
            log_record['message'] = record.getMessage()


class TextFormatter(logging.Formatter):
    """Human-readable text formatter with optional colors.
    
    Outputs logs in a readable format for development and console viewing.
    
    Format: timestamp | LEVEL | module.function | message | context
    Example: 2024-06-18 10:30:45 | INFO | github.get_pr_diff | Fetching PR diff | repo=owner/repo pr=42
    """
    
    # ANSI color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        """Initialize the text formatter.
        
        Args:
            use_colors: Whether to use ANSI color codes in output
        """
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and context.
        
        Args:
            record: Python logging.LogRecord object
            
        Returns:
            Formatted log string
        """
        # Add context to the message
        context = get_all_context()
        if context:
            context_str = ' | ' + ' '.join(f"{k}={v}" for k, v in context.items())
            record.msg = str(record.msg) + context_str
        
        # Add environment info
        record.msg = str(record.msg) + f" | env={LoggingConfig.ENVIRONMENT}"
        
        # Format the base message
        formatted = super().format(record)
        
        # Add colors if enabled
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted
