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
    gets restored to its previous state when exiting the block. This enables
    proper nesting of context managers without losing outer context.
    
    Example:
        with LoggingContext(repo_name="owner/repo", pr_number=42):
            # All logs in this block will include repo_name and pr_number
            logger.info("Processing PR")
            
            with LoggingContext(pr_number=43):
                # Inner context temporarily changes pr_number
                logger.info("Processing another PR")
            
            # After exiting inner context, pr_number is restored to 42
            logger.info("Back to original PR")
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize the context manager.
        
        Args:
            **kwargs: Context variables to set (repo_name, pr_number, etc.)
        """
        self.context = kwargs
        self.tokens: Dict[str, Any] = {}
    
    def __enter__(self) -> 'LoggingContext':
        """Enter the context and set variables, storing tokens for restoration."""
        # Set new context and store tokens for restoration
        if 'request_id' in self.context:
            self.tokens['request_id'] = _request_id.set(self.context['request_id'])
        if 'repo_name' in self.context:
            self.tokens['repo_name'] = _repo_name.set(self.context['repo_name'])
        if 'pr_number' in self.context:
            self.tokens['pr_number'] = _pr_number.set(self.context['pr_number'])
        
        # Set any other custom context
        for key, value in self.context.items():
            if key not in ['request_id', 'repo_name', 'pr_number']:
                # For custom context, store previous value
                prev_custom = _custom_context.get().copy()
                prev_custom[key] = value
                self.tokens[f'custom_{key}'] = _custom_context.set(prev_custom)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous state using stored tokens."""
        # Restore context variables to their previous state
        if 'request_id' in self.tokens:
            _request_id.reset(self.tokens['request_id'])
        if 'repo_name' in self.tokens:
            _repo_name.reset(self.tokens['repo_name'])
        if 'pr_number' in self.tokens:
            _pr_number.reset(self.tokens['pr_number'])
        
        # Restore custom context variables
        for key, token in self.tokens.items():
            if key.startswith('custom_'):
                _custom_context.reset(token)
        
        return False
