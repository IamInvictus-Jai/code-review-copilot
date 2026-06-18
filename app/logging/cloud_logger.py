"""
Cloud logger stub for future AWS CloudWatch / GCP Cloud Logging integration.

This is a placeholder implementation that can be extended to support various
cloud logging services. Currently raises NotImplementedError to indicate
that cloud logging needs to be configured.
"""

from typing import Any


class CloudLogger:
    """Cloud logger stub following LoggerProtocol.
    
    This is a placeholder for future cloud logging integration. When you're ready
    to implement cloud logging, you can extend this class to support services like:
    
    - AWS CloudWatch Logs
    - GCP Cloud Logging (formerly Stackdriver)
    - Azure Monitor Logs
    - Datadog
    - Splunk
    - ELK Stack (Elasticsearch, Logstash, Kibana)
    
    Example AWS CloudWatch Integration:
    --------------------------------
    1. Install: pip install boto3
    2. Configure AWS credentials
    3. Use boto3.client('logs') to create log groups/streams
    4. Use put_log_events to send logs
    
    Example GCP Cloud Logging Integration:
    -------------------------------------
    1. Install: pip install google-cloud-logging
    2. Configure GCP credentials
    3. Use google.cloud.logging.Client()
    4. Use logger.log_struct() for structured logs
    
    Example implementation snippet:
    -----------------------------
    ```python
    import boto3
    
    class CloudLogger:
        def __init__(self, name: str):
            self.client = boto3.client('logs', region_name='us-east-1')
            self.log_group = 'code-review-copilot'
            self.log_stream = name
            self._ensure_log_stream_exists()
        
        def info(self, message: str, **context: Any):
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps({'message': message, **context})
                }]
            )
    ```
    """
    
    def __init__(self, name: str):
        """Initialize the cloud logger stub.
        
        Args:
            name: Logger name (typically __name__ from calling module)
        
        Raises:
            NotImplementedError: Cloud logging is not yet configured
        """
        self.name = name
        self._raise_not_implemented()
    
    def _raise_not_implemented(self) -> None:
        """Raise NotImplementedError with helpful message."""
        raise NotImplementedError(
            "Cloud logging is not yet implemented. "
            "To enable cloud logging:\n"
            "1. Choose a cloud provider (AWS CloudWatch, GCP Cloud Logging, etc.)\n"
            "2. Install the appropriate SDK (boto3, google-cloud-logging, etc.)\n"
            "3. Configure credentials and permissions\n"
            "4. Implement the CloudLogger class in app/logging/cloud_logger.py\n"
            "5. Set LOG_TYPE=cloud in your environment variables\n\n"
            "See the docstring in cloud_logger.py for implementation examples."
        )
    
    def debug(self, message: str, **context: Any) -> None:
        """Log a debug-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
            
        Raises:
            NotImplementedError: Cloud logging not configured
        """
        self._raise_not_implemented()
    
    def info(self, message: str, **context: Any) -> None:
        """Log an info-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
            
        Raises:
            NotImplementedError: Cloud logging not configured
        """
        self._raise_not_implemented()
    
    def warning(self, message: str, **context: Any) -> None:
        """Log a warning-level message with optional context.
        
        Args:
            message: The log message
            **context: Additional context fields
            
        Raises:
            NotImplementedError: Cloud logging not configured
        """
        self._raise_not_implemented()
    
    def error(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log an error-level message with optional exception info and context.
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
            
        Raises:
            NotImplementedError: Cloud logging not configured
        """
        self._raise_not_implemented()
    
    def critical(
        self, 
        message: str, 
        exc_info: bool = False, 
        **context: Any
    ) -> None:
        """Log a critical-level message with optional exception info and context.
        
        Args:
            message: The log message
            exc_info: If True, include exception traceback in output
            **context: Additional context fields
            
        Raises:
            NotImplementedError: Cloud logging not configured
        """
        self._raise_not_implemented()
