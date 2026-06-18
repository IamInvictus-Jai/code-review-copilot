"""
Logging package for Code Review Copilot.

This package provides a protocol-based logging system that allows easy switching
between different logging backends (console, file, cloud).

Usage:
    from app.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Application started", version="1.0.0")
"""

from app.logging.logger_protocol import LoggerProtocol
from app.logging.logger_factory import get_logger

__all__ = ["LoggerProtocol", "get_logger"]
