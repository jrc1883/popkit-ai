"""
PopKit Storage Abstractions

Generic interfaces for storage backends including:
- Redis (local, Upstash, ElastiCache, etc.)
- File-based storage
- Cloud storage

These abstractions allow PopKit to work with multiple storage backends
without changing the core logic.
"""

from .redis_interface import BaseRedisClient, BasePubSub

__all__ = ["BaseRedisClient", "BasePubSub"]
