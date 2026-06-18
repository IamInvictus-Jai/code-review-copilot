"""
Abstract logger protocol defining the interface for all logger implementations.

This module provides a Protocol class that defines the contract all logger
implementations must follow. This allows easy switching between different
logging backends without changing calling code.
"""

from typing import Protocol, Any


class LoggerProtocol(Protocol):
    """Abstract interface for logger implementations.
    
    This protocol defines the standard logging interface that all logger
    implementations must follow. It uses Python's typing.Protocol to create
    a structural subtype (similar to interfaces in Java).
    
    Any class implementing these methods with matching signatures will be
    considered a valid LoggerProtocol, enabling easy switching between
    console, file, and cloud logging backends.
    
    All logging methods accept arbitrary keyword arguments as 'context'
    which will be included in structured log output.
    """
    
    def debug(self, message: str, **context: Any) -> None:
        """Log a debug-level message with optional context.
        
        Use for detailed diagnostic information useful during development
        and troubleshooting. Typically disabled in production.
        
        Args:
            message: The log message
            **context: Additional context fields (repo_name, pr_number, etc.)
            
        Example:
            logger.debug("Starting operation", repo_name="owner/repo", pr_number=42)
        """
        ...
    
    def info(self, message: str, **context: Any) -> None:
        """Log an info-level message with optional context.
        
        Use for general informational messages about normal operations.
        
        Args:
            message: The log message
            **context: Additional context fields
            
        Example:
            logger.info("PR analysis completed", risk_score=3, duration_ms=1234)
        """
        ...
    
    def warning(self, message: str, **context: Any) -> None:
        """Log a warning-level message with optional context.
        
        Use for unexpected situations that were handled gracefully but may
        indicate a problem (e.g., API rate limits, fallback logic triggered).
        
        Args:
            message: The log message
            **context: Additional context fields
            
        Example:
            logger.warning("API rate limit reached", fallback_used=True)
        """
        ...
    
    def error(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log an error-level message with optional exception info and context.
        
        Use when an operation fails. Set exc_info=True to include full stack trace.
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
            
        Example:
            try:
                result = risky_operation()
            except Exception:
                logger.error("Operation failed", exc_info=True, operation="fetch_pr")
        """
        ...
    
    def critical(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log a critical-level message with optional exception info and context.
        
        Use for system-level failures that prevent the application from functioning
        (e.g., database unreachable, invalid configuration, missing API keys).
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
            
        Example:
            logger.critical("Database connection failed", exc_info=True)
        """
        ...
