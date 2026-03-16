"""
cache_service.py — Caching Layer
===================================

Provides a caching interface for frequently accessed data:
- Hotspot queries by bounding box
- Ocean data lookups
- Prediction results

Supports Redis (production) and in-memory dict (development).
"""

import json
import hashlib
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)

# In-memory cache for development (replace with Redis in production)
_memory_cache: dict[str, Any] = {}


def _make_key(*args: Any) -> str:
    """Generate a stable cache key from arguments."""
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


async def get_cached(namespace: str, *key_parts: Any) -> Optional[Any]:
    """
    Retrieve a value from cache.

    Args:
        namespace: Cache namespace (e.g., "hotspots", "ocean_data")
        key_parts: Values used to build the cache key

    Returns:
        Cached value or None if not found
    """
    key = f"{namespace}:{_make_key(*key_parts)}"

    # TODO: Use Redis in production
    # value = await redis_client.get(key)

    value = _memory_cache.get(key)
    if value is not None:
        logger.debug("Cache hit", namespace=namespace)
    return value


async def set_cached(
    namespace: str,
    *key_parts: Any,
    value: Any,
    ttl_seconds: int = 300,
) -> None:
    """
    Store a value in cache.

    Args:
        namespace: Cache namespace
        key_parts: Values used to build the cache key
        value: Value to cache
        ttl_seconds: Time-to-live in seconds (default: 5 minutes)
    """
    key = f"{namespace}:{_make_key(*key_parts)}"

    # TODO: Use Redis with TTL in production
    # await redis_client.setex(key, ttl_seconds, json.dumps(value))

    _memory_cache[key] = value
    logger.debug("Cache set", namespace=namespace, ttl=ttl_seconds)


async def invalidate(namespace: str) -> None:
    """
    Invalidate all cached entries in a namespace.

    Called when new predictions are generated to ensure
    fresh data is served.
    """
    # TODO: Use Redis SCAN + DEL pattern in production
    keys_to_delete = [k for k in _memory_cache if k.startswith(f"{namespace}:")]
    for key in keys_to_delete:
        del _memory_cache[key]
    logger.info("Cache invalidated", namespace=namespace, keys=len(keys_to_delete))
