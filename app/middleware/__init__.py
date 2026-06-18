"""
Middleware package for Code Review Copilot.

This package provides FastAPI middleware for:
- Global exception handling
- Request/response logging
- Request ID generation
"""

from app.middleware.error_handler import setup_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware

__all__ = ["setup_exception_handlers", "LoggingMiddleware"]
