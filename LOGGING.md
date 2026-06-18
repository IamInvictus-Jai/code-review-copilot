# Logging System Documentation

## Overview

The Code Review Copilot uses a comprehensive, protocol-based logging system that provides:
- Structured logging with JSON or text output
- Multiple backends (console, file, cloud-ready)
- Automatic request tracking with unique IDs
- Context propagation across async operations
- Performance metrics and timing
- Full exception tracing

## Architecture

### Components

```
LoggerProtocol (Interface)
    ├── ConsoleLogger    → stdout/stderr with colors
    ├── FileLogger       → rotating files with JSON
    └── CloudLogger      → stub for AWS/GCP (future)

LoggerFactory
    └── get_logger(name) → returns appropriate logger

LoggingContext
    ├── request_id       → unique request identifier
    ├── repo_name        → repository being processed
    └── pr_number        → PR being reviewed

Middleware
    ├── LoggingMiddleware      → request/response logging
    └── ErrorHandlerMiddleware → global exception handling
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Log Level
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log Type
LOG_TYPE=console                    # console, file, both, cloud

# File Logging (when LOG_TYPE=file or both)
LOG_FILE_PATH=logs/app.log
LOG_FILE_MAX_SIZE=10485760         # 10MB in bytes
LOG_FILE_BACKUP_COUNT=5

# Log Format
LOG_FORMAT=json                     # json (structured) or text (human-readable)

# Environment
ENVIRONMENT=development             # development or production
```

### Log Levels Explained

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info | Function entry/exit, variable values, step-by-step progress |
| **INFO** | General informational | PR received, review completed, operations successful |
| **WARNING** | Unexpected but handled | API rate limit, fallback used, missing config |
| **ERROR** | Operation failed | Couldn't post comment, API error, parsing failure |
| **CRITICAL** | System-level failure | DB unreachable, invalid config, missing API keys |

## Usage

### Basic Usage

```python
from app.logging import get_logger

# Create logger (typically at module level)
logger = get_logger(__name__)

# Log messages with context
logger.info("Processing PR", extra={"repo_name": "owner/repo", "pr_number": 42})
logger.warning("Rate limit approaching", extra={"remaining": 10})
logger.error("Operation failed", exc_info=True, extra={"operation": "fetch_pr"})
```

### With Exception Handling

```python
from app.logging import get_logger

logger = get_logger(__name__)

def process_data(data):
    logger.info("Starting data processing", extra={"data_size": len(data)})
    
    try:
        result = risky_operation(data)
        logger.info("Processing successful", extra={"result_count": len(result)})
        return result
        
    except SpecificError as e:
        logger.warning("Handled specific error", exc_info=True, extra={"fallback": True})
        return fallback_result()
        
    except Exception as e:
        logger.error("Unexpected error", exc_info=True, extra={"data_size": len(data)})
        raise
```

### With Context Propagation

```python
from app.logging import get_logger
from app.logging.context import set_request_id, set_repo_name, set_pr_number

logger = get_logger(__name__)

def handle_webhook(repo_name, pr_number):
    # Set context once - all subsequent logs will include it
    set_request_id()  # Auto-generates unique ID
    set_repo_name(repo_name)
    set_pr_number(pr_number)
    
    # All logs now include repo_name and pr_number automatically
    logger.info("Processing webhook")
    process_pr()
    logger.info("Webhook processing complete")
```

### Performance Timing

```python
import time
from app.logging import get_logger

logger = get_logger(__name__)

def expensive_operation():
    start_time = time.time()
    
    logger.debug("Starting expensive operation")
    
    try:
        result = do_work()
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Operation completed",
            extra={"duration_ms": duration_ms, "result_count": len(result)}
        )
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "Operation failed",
            exc_info=True,
            extra={"duration_ms": duration_ms}
        )
        raise
```

## Log Output Formats

### JSON Format (Structured)

Used for machine parsing and log aggregation tools:

```json
{
  "message": "PR analysis completed",
  "timestamp": 1781772327.113,
  "level": "INFO",
  "module": "reviewer",
  "function": "analyze_pr_diff",
  "environment": "development",
  "request_id": "req_abc123def456",
  "repo_name": "owner/repo",
  "pr_number": 42,
  "risk_score": 3,
  "duration_ms": 1234
}
```

### Text Format (Human-Readable)

Used for console viewing during development:

```
2024-06-18 10:30:45 | INFO     | reviewer.analyze_pr_diff | PR analysis completed | request_id=req_abc123def456 repo_name=owner/repo pr_number=42 risk_score=3 duration_ms=1234 | env=development
```

## Switching Between Backends

### Console Only (Development)

```env
LOG_TYPE=console
LOG_FORMAT=text
```

Good for: Local development, debugging

### File Only (Production)

```env
LOG_TYPE=file
LOG_FORMAT=json
LOG_FILE_PATH=logs/app.log
```

Good for: Production deployments, audit trails

### Both Console and File

```env
LOG_TYPE=both
LOG_FORMAT=json
```

Good for: Debugging production issues, seeing logs in real-time while also saving them

### Cloud Logging (Future)

```env
LOG_TYPE=cloud
# Requires implementation - see app/logging/cloud_logger.py
```

## Request Tracking

Every API request gets a unique request ID that propagates through all operations:

```json
{
  "request_id": "req_abc123def456",
  "message": "Incoming request",
  "path": "/webhook/github",
  "method": "POST"
}

{
  "request_id": "req_abc123def456",
  "message": "Fetching PR diff",
  "repo_name": "owner/repo",
  "pr_number": 42
}

{
  "request_id": "req_abc123def456",
  "message": "Request completed",
  "status_code": 200,
  "duration_ms": 1234
}
```

Trace any request end-to-end by filtering on `request_id`.

## Middleware

### Logging Middleware

Automatically logs all incoming requests and outgoing responses:

- Generates unique request ID
- Logs request method, path, client IP
- Measures request duration
- Adds `X-Request-ID` header to responses

### Error Handler Middleware

Catches all unhandled exceptions:

- Logs with full stack trace
- Returns clean error responses
- Hides internals in production
- Includes request ID for tracing

## Best Practices

### Do ✅

```python
# Use structured logging with context
logger.info("Operation completed", extra={"count": 10, "type": "users"})

# Always include exc_info for errors
logger.error("Failed to connect", exc_info=True, extra={"host": "api.example.com"})

# Use appropriate log levels
logger.debug("Variable value: %s", value)  # Only in DEBUG mode
logger.info("User logged in")              # Normal operations
logger.warning("Retry attempt 3/5")        # Handled issues
logger.error("Database query failed")      # Operation failures

# Log function entry/exit for debugging
logger.debug("Entering complex_function", extra={"param": value})
# ... do work ...
logger.debug("Exiting complex_function", extra={"result": success})
```

### Don't ❌

```python
# Don't use print() - use logger instead
print("Processing...")  # ❌ Bad

# Don't log without context
logger.info("Processing")  # ❌ Too vague

# Don't forget exc_info for exceptions
logger.error(str(e))  # ❌ Missing stack trace

# Don't log sensitive data
logger.info(f"API key: {api_key}")  # ❌ Security risk

# Don't use silent exception handling
except Exception:
    pass  # ❌ Hides errors
```

## Troubleshooting

### Logs Not Appearing

**Problem**: Logger configured but logs not showing

**Solutions**:
1. Check `LOG_LEVEL` - DEBUG logs won't show if level is INFO
2. Verify logger is imported: `from app.logging import get_logger`
3. Check `LOG_TYPE` environment variable
4. For file logs, verify `logs/` directory is writable

### Log File Growing Too Large

**Problem**: Log files consuming too much disk space

**Solutions**:
1. Decrease `LOG_FILE_MAX_SIZE` (default 10MB)
2. Decrease `LOG_FILE_BACKUP_COUNT` (default 5)
3. Set higher `LOG_LEVEL` (INFO instead of DEBUG)
4. Use log rotation tools (logrotate on Linux)

### Context Not Propagating

**Problem**: `repo_name` or `pr_number` not appearing in logs

**Solutions**:
1. Ensure context is set: `set_repo_name(repo)` before logging
2. Use `LoggingContext` context manager for automatic cleanup
3. Check you're using structured logger (`get_logger`) not basic `logging`

### Performance Impact

**Problem**: Logging slowing down application

**Solutions**:
1. Use `LOG_TYPE=file` instead of `both` (file-only is faster)
2. Increase `LOG_LEVEL` to reduce volume (INFO or WARNING)
3. Use `LOG_FORMAT=json` (faster than text formatting)
4. Reduce debug logging in production

## Extending the System

### Adding Cloud Logging

To implement AWS CloudWatch or GCP Cloud Logging:

1. Install SDK: `pip install boto3` (AWS) or `pip install google-cloud-logging` (GCP)
2. Edit `app/logging/cloud_logger.py`
3. Implement the `CloudLogger` class methods
4. Configure credentials and permissions
5. Set `LOG_TYPE=cloud` in environment

See `app/logging/cloud_logger.py` for implementation examples.

### Custom Formatters

Create custom formatters by extending `logging.Formatter`:

```python
from app.logging.formatters import JsonFormatter

class CustomFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Add custom fields
        log_record['custom_field'] = 'value'
```

## Examples

### Example 1: Service Function

```python
from app.logging import get_logger

logger = get_logger(__name__)

def fetch_user_data(user_id: str):
    logger.info("Fetching user data", extra={"user_id": user_id})
    
    try:
        data = api.get_user(user_id)
        logger.info(
            "User data fetched successfully",
            extra={"user_id": user_id, "data_size": len(data)}
        )
        return data
    except APIError as e:
        logger.error(
            "Failed to fetch user data",
            exc_info=True,
            extra={"user_id": user_id, "api_status": e.status_code}
        )
        raise
```

### Example 2: FastAPI Endpoint

```python
from fastapi import FastAPI
from app.logging import get_logger
from app.logging.context import set_repo_name, set_pr_number

logger = get_logger(__name__)
app = FastAPI()

@app.post("/process")
async def process_request(repo_name: str, pr_number: int):
    logger.info("Processing request", extra={"repo_name": repo_name, "pr_number": pr_number})
    
    # Set context for all subsequent logs
    set_repo_name(repo_name)
    set_pr_number(pr_number)
    
    result = process_data(repo_name, pr_number)
    
    logger.info("Request processed successfully", extra={"result_count": len(result)})
    return {"status": "success", "data": result}
```

## Summary

The logging system provides:

✅ **Structured Logging** - JSON format for easy parsing  
✅ **Multiple Backends** - Console, file, and cloud-ready  
✅ **Request Tracking** - Unique IDs for end-to-end tracing  
✅ **Context Propagation** - Automatic context in all logs  
✅ **Performance Metrics** - Built-in timing and statistics  
✅ **Exception Tracing** - Full stack traces with context  
✅ **Production Ready** - Rotation, levels, and environment-aware  
✅ **Easy to Extend** - Protocol-based design for new backends  

For questions or issues, check the troubleshooting section or review the implementation in `app/logging/`.
