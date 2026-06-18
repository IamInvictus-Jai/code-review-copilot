"""
Centralized configuration for the Code Review Copilot application.

This module provides configuration classes that load settings from environment
variables, with sensible defaults for development.
"""

import os
from typing import Literal


class LoggingConfig:
    """Centralized logging configuration from environment variables.
    
    All logging-related settings are defined here and loaded from the environment.
    This allows easy configuration changes without code modifications.
    
    Attributes:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_TYPE: Where to send logs (console, file, both, cloud)
        LOG_FILE_PATH: Path to log file for file-based logging
        LOG_FILE_MAX_BYTES: Maximum size of log file before rotation
        LOG_FILE_BACKUP_COUNT: Number of backup log files to keep
        LOG_FORMAT: Output format (json for structured, text for human-readable)
        ENVIRONMENT: Current environment (development, production)
    """
    
    # Log level - controls verbosity
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Log type - where logs are sent
    LOG_TYPE: Literal["console", "file", "both", "cloud"] = os.getenv("LOG_TYPE", "console")
    
    # File logging settings
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    LOG_FILE_MAX_BYTES: int = int(os.getenv("LOG_FILE_MAX_SIZE", "10485760"))  # 10MB default
    LOG_FILE_BACKUP_COUNT: int = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
    
    # Format - json for machines, text for humans
    LOG_FORMAT: Literal["json", "text"] = os.getenv("LOG_FORMAT", "json")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def validate(cls) -> None:
        """Validate logging configuration.
        
        Raises:
            ValueError: If any configuration value is invalid
        """
        # Validate LOG_LEVEL
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL: {cls.LOG_LEVEL}. "
                f"Must be one of {valid_levels}"
            )
        
        # Validate LOG_TYPE
        valid_types = ["console", "file", "both", "cloud"]
        if cls.LOG_TYPE not in valid_types:
            raise ValueError(
                f"Invalid LOG_TYPE: {cls.LOG_TYPE}. "
                f"Must be one of {valid_types}"
            )
        
        # Validate LOG_FORMAT
        valid_formats = ["json", "text"]
        if cls.LOG_FORMAT not in valid_formats:
            raise ValueError(
                f"Invalid LOG_FORMAT: {cls.LOG_FORMAT}. "
                f"Must be one of {valid_formats}"
            )
    
    @classmethod
    def get_log_level_int(cls) -> int:
        """Convert LOG_LEVEL string to logging module integer constant.
        
        Returns:
            Integer constant from logging module (e.g., logging.INFO = 20)
        """
        import logging
        return getattr(logging, cls.LOG_LEVEL, logging.INFO)


# Validate configuration on import
LoggingConfig.validate()
