"""
Request/response logging middleware for FastAPI.

This middleware automatically logs all incoming requests and outgoing responses,
including timing information and request IDs for tracing.
"""

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging import get_logger
from app.logging.context import set_request_id, generate_request_id, clear_context

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic request/response logging.
    
    This middleware:
    - Generates a unique request ID for each request
    - Sets request ID in logging context
    - Logs incoming request details
    - Measures request duration
    - Logs outgoing response with status and timing
    - Cleans up context after request
    
    The request ID can be used to trace a single request through the entire
    system, including all service calls and database operations.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add logging.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Generate unique request ID
        request_id = generate_request_id()
        
        # Store request ID in request state for access in handlers
        request.state.request_id = request_id
        
        # Set request ID in logging context
        set_request_id(request_id)
        
        # Log incoming request
        start_time = time.time()
        
        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params) if request.query_params else None,
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # If an exception occurs, log it and re-raise
            # (it will be caught by exception handlers)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Request processing failed",
                exc_info=True,
                extra={
                    "duration_ms": duration_ms
                }
            )
            raise
        
        # Calculate request duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log outgoing response
        log_level = "info" if response.status_code < 400 else "warning"
        log_method = getattr(logger, log_level)
        
        log_method(
            "Request completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }
        )
        
        # Clean up context for next request
        clear_context()
        
        return response
