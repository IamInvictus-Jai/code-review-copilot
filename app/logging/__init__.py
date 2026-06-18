"""
Logging package for Code Review Copilot.

This package provides a protocol-based logging system that allows easy switching
between different logging backends (console, file, cloud).
"""

from app.logging.logger_protocol import LoggerProtocol

__all__ = ["LoggerProtocol"]
