"""Rate limiting functionality for authentication endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings


class SimpleInMemoryRateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.
    
    Thread-safe for basic cases. For production, use Redis-based rate limiting.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address, email)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return True

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Get existing requests for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] if req_time > cutoff
        ]

        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Record new request
        self.requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return self.max_requests

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        if identifier not in self.requests:
            return self.max_requests

        # Count requests within window
        active_requests = sum(
            1 for req_time in self.requests[identifier] if req_time > cutoff
        )

        return max(0, self.max_requests - active_requests)


# Global rate limiters
auth_rate_limiter = SimpleInMemoryRateLimiter(max_requests=5, window_seconds=60)
api_rate_limiter = SimpleInMemoryRateLimiter(
    max_requests=60, window_seconds=60
)


def check_rate_limit(identifier: str, limiter: SimpleInMemoryRateLimiter) -> bool:
    """
    Check if a request is allowed by the rate limiter.
    
    Args:
        identifier: Unique identifier for rate limiting
        limiter: Rate limiter instance
        
    Returns:
        True if allowed, False if rate limited
    """
    return limiter.is_allowed(identifier)
