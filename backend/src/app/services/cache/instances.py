"""
Pre-configured cache instances for common use cases.

Provides singleton cache instances with appropriate namespaces and TTLs
for different application features.

Usage:
    from app.services.cache.instances import confirmation_cache, signup_cache
    
    # Store a confirmation
    await confirmation_cache.set("action_123", action_data, ttl=300)
    
    # Get a signup session
    session = await signup_cache.get("session_abc")
"""

from app.services.cache import CacheFactory
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize cache instances
logger.info("Initializing cache instances...")

# Confirmation cache - for pending confirmations (5 min TTL)
confirmation_cache = CacheFactory.create_cache(
    namespace="confirmation",
    default_ttl=300  # 5 minutes
)
logger.info("✅ confirmation_cache initialized")

# Signup cache - for signup sessions (30 min TTL)
signup_cache = CacheFactory.create_cache(
    namespace="signup",
    default_ttl=1800  # 30 minutes
)
logger.info("✅ signup_cache initialized")

# Session cache - for user sessions (24 hour TTL)
session_cache = CacheFactory.create_cache(
    namespace="session",
    default_ttl=86400  # 24 hours
)
logger.info("✅ session_cache initialized")

# Rate limit cache - for rate limiting (1 hour TTL)
rate_limit_cache = CacheFactory.create_cache(
    namespace="rate_limit",
    default_ttl=3600  # 1 hour
)
logger.info("✅ rate_limit_cache initialized")

# Temporary cache - for short-lived data (1 min TTL)
temp_cache = CacheFactory.create_cache(
    namespace="temp",
    default_ttl=60  # 1 minute
)
logger.info("✅ temp_cache initialized")

__all__ = [
    "confirmation_cache",
    "signup_cache",
    "session_cache",
    "rate_limit_cache",
    "temp_cache",
]

logger.info("All cache instances initialized successfully")
