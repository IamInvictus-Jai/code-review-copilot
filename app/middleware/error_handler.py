"""
Global exception handler for FastAPI application.

This module provides centralized exception handling that catches all unhandled
errors, logs them with full context, and returns clean error responses.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.config import LoggingConfig
from app.logging import get_logger
from app.logging.context import get_request_id

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException errors.
    
    These are expected errors raised by the application (e.g., 404, 401, 400).
    Log them at warning level since they're typically client errors.
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSON response with error details
    """
    request_id = get_request_id() or "unknown"
    
    logger.warning(
        f"HTTP {exc.status_code} error",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors.
    
    These occur when request data doesn't match Pydantic model requirements.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSON response with validation error details
    """
    request_id = get_request_id() or "unknown"
    
    logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions.
    
    This is the catch-all handler for unexpected errors. Logs full stack trace
    and returns different responses for dev vs production.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSON response with error information
    """
    request_id = get_request_id() or "unknown"
    
    # Log with full context and stack trace
    logger.error(
        "Unhandled exception in request",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Return different responses based on environment
    if LoggingConfig.ENVIRONMENT == "production":
        # Hide internal error details in production
        detail = "Internal server error"
        error_type = "InternalError"
    else:
        # Show detailed error in development
        detail = str(exc)
        error_type = type(exc).__name__
    
    return JSONResponse(
        status_code=500,
        content={
            "error": detail,
            "error_type": error_type,
            "request_id": request_id
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.
    
    This should be called during application startup to ensure all exceptions
    are properly caught and logged.
    
    Args:
        app: FastAPI application instance
        
    Example:
        app = FastAPI()
        setup_exception_handlers(app)
    """
    # Handle HTTP exceptions (404, 401, etc.)
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Handle request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all for any other exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")
