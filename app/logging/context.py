"""
Logging context manager for request tracking and context propagation.

This module provides thread-safe context storage using Python's contextvars.
Context variables (like request_id, repo_name, pr_number) are automatically
included in all log messages within the same execution context.
"""

import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional


# Context variables for request tracking
# These are thread-safe and work correctly with async code
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_repo_name: ContextVar[Optional[str]] = ContextVar('repo_name', default=None)
_pr_number: ContextVar[Optional[int]] = ContextVar('pr_number', default=None)
_custom_context: ContextVar[Dict[str, Any]] = ContextVar('custom_context', default={})


def generate_request_id() -> str:
    """Generate a unique request ID.
    
    Returns:
        UUID string in format: "req_abc123def456"
    """
    return f"req_{uuid.uuid4().hex[:12]}"


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set the request ID for the current context.
    
    Args:
        request_id: Request ID to set. If None, generates a new one.
        
    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = generate_request_id()
    _request_id.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get the current request ID.
    
    Returns:
        Current request ID or None if not set
    """
    return _request_id.get()


def set_repo_name(repo_name: str) -> None:
    """Set the repository name for the current context.
    
    Args:
        repo_name: Repository name in format "owner/repo"
    """
    _repo_name.set(repo_name)


def get_repo_name() -> Optional[str]:
    """Get the current repository name.
    
    Returns:
        Current repository name or None if not set
    """
    return _repo_name.get()


def set_pr_number(pr_number: int) -> None:
    """Set the PR number for the current context.
    
    Args:
        pr_number: Pull request number
    """
    _pr_number.set(pr_number)


def get_pr_number() -> Optional[int]:
    """Get the current PR number.
    
    Returns:
        Current PR number or None if not set
    """
    return _pr_number.get()


def set_context(key: str, value: Any) -> None:
    """Set a custom context variable.
    
    Args:
        key: Context variable name
        value: Context variable value
    """
    current = _custom_context.get().copy()
    current[key] = value
    _custom_context.set(current)


def get_context(key: str) -> Optional[Any]:
    """Get a custom context variable.
    
    Args:
        key: Context variable name
        
    Returns:
        Context variable value or None if not set
    """
    return _custom_context.get().get(key)


def get_all_context() -> Dict[str, Any]:
    """Get all context variables as a dictionary.
    
    This is used by formatters to automatically include context in logs.
    
    Returns:
        Dictionary of all context variables with values
    """
    context = {}
    
    # Add standard context variables if set
    request_id = get_request_id()
    if request_id:
        context['request_id'] = request_id
    
    repo_name = get_repo_name()
    if repo_name:
        context['repo_name'] = repo_name
    
    pr_number = get_pr_number()
    if pr_number is not None:
        context['pr_number'] = pr_number
    
    # Add custom context variables
    custom = _custom_context.get()
    if custom:
        context.update(custom)
    
    return context


def clear_context() -> None:
    """Clear all context variables.
    
    Useful for cleanup between requests or tests.
    """
    _request_id.set(None)
    _repo_name.set(None)
    _pr_number.set(None)
    _custom_context.set({})


class LoggingContext:
    """Context manager for setting logging context.
    
    This allows using 'with' statements to set context that automatically
    gets cleaned up when exiting the block.
    
    Example:
        with LoggingContext(repo_name="owner/repo", pr_number=42):
            # All logs in this block will include repo_name and pr_number
            logger.info("Processing PR")
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize the context manager.
        
        Args:
            **kwargs: Context variables to set (repo_name, pr_number, etc.)
        """
        self.context = kwargs
        self.previous_context: Dict[str, Any] = {}
    
    def __enter__(self) -> 'LoggingContext':
        """Enter the context and set variables."""
        # Save previous context
        self.previous_context = get_all_context()
        
        # Set new context
        if 'request_id' in self.context:
            set_request_id(self.context['request_id'])
        if 'repo_name' in self.context:
            set_repo_name(self.context['repo_name'])
        if 'pr_number' in self.context:
            set_pr_number(self.context['pr_number'])
        
        # Set any other custom context
        for key, value in self.context.items():
            if key not in ['request_id', 'repo_name', 'pr_number']:
                set_context(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous variables."""
        # This could restore previous context, but for now we just clear
        # to avoid context leaking between requests
        clear_context()
        return False
