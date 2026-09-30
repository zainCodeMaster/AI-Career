"""Application logging configuration and utilities."""

import logging
import sys
from typing import Any

from app.core.config import get_settings


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def configure_logging() -> None:
    """Configure application-wide logging with safe defaults."""
    settings = get_settings()
    
    # Create logger for CareerOS app
    logger = logging.getLogger("app")
    
    # Only configure if not already configured
    if logger.handlers:
        return
    
    # Set log level based on DEBUG setting
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter - simple format by default, more verbose in debug
    if settings.debug:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_auth_event(
    event_type: str,
    email: str = None,
    success: bool = None,
    details: dict = None,
) -> None:
    """
    Log authentication-related events safely.
    
    Never logs passwords, password hashes, or sensitive credentials.
    
    Args:
        event_type: Type of event (LOGIN_ATTEMPT, REGISTRATION, etc.)
        email: Email address (optional, used for correlation)
        success: Whether the event succeeded (optional)
        details: Additional non-sensitive details (optional)
    """
    logger = get_logger("app.auth")
    
    # Build safe log message
    message = f"{event_type}"
    if email:
        message += f" for {email}"
    if success is not None:
        message += f" (success={success})"
    
    # Log at appropriate level
    if success is False:
        logger.warning(message, extra={"details": details or {}})
    else:
        logger.info(message, extra={"details": details or {}})


def log_api_event(
    event_type: str,
    endpoint: str = None,
    status_code: int = None,
    details: dict = None,
) -> None:
    """
    Log API-related events safely.
    
    Args:
        event_type: Type of event (REQUEST_ERROR, VALIDATION_ERROR, etc.)
        endpoint: API endpoint path
        status_code: HTTP status code (optional)
        details: Additional non-sensitive details (optional)
    """
    logger = get_logger("app.api")
    
    message = f"{event_type}"
    if endpoint:
        message += f" {endpoint}"
    if status_code:
        message += f" (status={status_code})"
    
    logger.warning(message, extra={"details": details or {}})


def sanitize_for_log(data: dict[str, Any]) -> dict[str, Any]:
    """
    Remove sensitive fields from a dictionary before logging.
    
    Redacts:
    - password, password_hash
    - token, access_token, jwt
    - secret, api_key
    - authorization, cookie
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        New dictionary with sensitive fields redacted
    """
    sensitive_keys = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "jwt",
        "secret",
        "api_key",
        "authorization",
        "cookie",
        "auth_header",
        "secret_key",
    }
    
    return {
        k: "***REDACTED***" if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }
