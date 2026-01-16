"""
Generic Redis Client Abstraction

This module provides abstract base classes for Redis clients that work with
ANY Redis implementation - local Redis, Upstash, ElastiCache, Redis Cloud, etc.

The interfaces abstract away implementation details so that PopKit features can
work seamlessly with different Redis backends without code changes.

Usage:
    class MyRedisClient(BaseRedisClient):
        # Implement all abstract methods for your specific backend
        pass

Implementations:
    - UpstashRedisClient (packages/popkit-core/power-mode/upstash_adapter.py)
    - LocalRedisClient (future - for local Redis)
    - ElastiCacheClient (future - for AWS ElastiCache)

Original Source:
    Extracted from packages/popkit-core/power-mode/upstash_adapter.py
    during Epic #580 cleanup (2025-12-29)

    Only the generic interface abstractions were moved to shared-py.
    The Upstash-specific implementations remain in power-mode.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# =============================================================================
# ABSTRACT BASE CLIENT
# =============================================================================


class BaseRedisClient(ABC):
    """
    Abstract base for Redis clients.

    This interface defines the core Redis operations that all implementations
    must support. It includes:
    - Basic key-value operations (get, set, delete)
    - Hash operations (hset, hget, hgetall)
    - List operations (rpush, lpush, lrange)
    - Pub/sub operations (publish, subscribe via pubsub())
    - Stream operations (xadd, xread, xrange)

    All methods are abstract - subclasses must implement them for their
    specific backend (REST API, socket connection, etc.).
    """

    @abstractmethod
    def ping(self) -> bool:
        """
        Check connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set a key-value pair with optional expiration.

        Args:
            key: Key name
            value: Value to store
            ex: Optional expiration in seconds

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get a value by key.

        Args:
            key: Key name

        Returns:
            Value if exists, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            *keys: Key names to delete

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            *keys: Key names to check

        Returns:
            Number of keys that exist
        """
        pass

    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: Glob pattern (default "*" for all keys)

        Returns:
            List of matching keys
        """
        pass

    # Hash operations
    @abstractmethod
    def hset(self, name: str, mapping: Dict[str, str]) -> int:
        """
        Set hash fields.

        Args:
            name: Hash name
            mapping: Field-value pairs

        Returns:
            Number of fields added
        """
        pass

    @abstractmethod
    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get hash field.

        Args:
            name: Hash name
            key: Field name

        Returns:
            Field value if exists, None otherwise
        """
        pass

    @abstractmethod
    def hgetall(self, name: str) -> Dict[str, str]:
        """
        Get all hash fields.

        Args:
            name: Hash name

        Returns:
            Dictionary of all field-value pairs
        """
        pass

    @abstractmethod
    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields.

        Args:
            name: Hash name
            *keys: Field names to delete

        Returns:
            Number of fields deleted
        """
        pass

    # List operations
    @abstractmethod
    def rpush(self, name: str, *values: str) -> int:
        """
        Push to end of list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of list after push
        """
        pass

    @abstractmethod
    def lpush(self, name: str, *values: str) -> int:
        """
        Push to start of list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of list after push
        """
        pass

    @abstractmethod
    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get list range.

        Args:
            name: List name
            start: Start index (0-based)
            end: End index (-1 for all)

        Returns:
            List of values in range
        """
        pass

    @abstractmethod
    def lpop(self, name: str) -> Optional[str]:
        """
        Pop from start of list.

        Args:
            name: List name

        Returns:
            Popped value if exists, None otherwise
        """
        pass

    # Expiration operations
    @abstractmethod
    def expire(self, name: str, time: int) -> bool:
        """
        Set key expiration.

        Args:
            name: Key name
            time: TTL in seconds

        Returns:
            True if expiration set successfully
        """
        pass

    @abstractmethod
    def ttl(self, name: str) -> int:
        """
        Get time to live.

        Args:
            name: Key name

        Returns:
            TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        pass

    # Pub/sub operations
    @abstractmethod
    def publish(self, channel: str, message: str) -> int:
        """
        Publish message to channel.

        Note: For Upstash REST API, this is simulated via Redis Streams.
        For local Redis, this uses native PUBSUB.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        pass

    @abstractmethod
    def pubsub(self) -> "BasePubSub":
        """
        Get pub/sub interface.

        Returns:
            Pub/sub client for subscribing to channels
        """
        pass

    # Stream operations (Redis Streams - native in Redis 5.0+)
    @abstractmethod
    def xadd(
        self, name: str, fields: Dict[str, str], id: str = "*", maxlen: Optional[int] = None
    ) -> str:
        """
        Add entry to stream.

        Args:
            name: Stream name
            fields: Field-value pairs
            id: Entry ID ("*" for auto-generated)
            maxlen: Maximum stream length (trim old entries)

        Returns:
            Entry ID
        """
        pass

    @abstractmethod
    def xread(
        self, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None
    ) -> List:
        """
        Read from streams.

        Args:
            streams: Dict of {stream_name: last_id}
            count: Maximum number of entries per stream
            block: Block for N milliseconds (None for non-blocking)

        Returns:
            List of stream entries
        """
        pass

    @abstractmethod
    def xrange(
        self, name: str, min: str = "-", max: str = "+", count: Optional[int] = None
    ) -> List:
        """
        Get stream range.

        Args:
            name: Stream name
            min: Minimum entry ID ("-" for oldest)
            max: Maximum entry ID ("+" for newest)
            count: Maximum number of entries

        Returns:
            List of stream entries
        """
        pass


# =============================================================================
# ABSTRACT PUB/SUB INTERFACE
# =============================================================================


class BasePubSub(ABC):
    """
    Abstract base for pub/sub interface.

    This interface defines the core pub/sub operations. Implementations can:
    - Use native Redis PUBSUB (local Redis)
    - Simulate pub/sub via Redis Streams (Upstash REST API)
    - Use message queues (RabbitMQ, etc.)
    """

    @abstractmethod
    def subscribe(self, *channels: str) -> None:
        """
        Subscribe to channels.

        Args:
            *channels: Channel names to subscribe to
        """
        pass

    @abstractmethod
    def unsubscribe(self, *channels: str) -> None:
        """
        Unsubscribe from channels.

        Args:
            *channels: Channel names to unsubscribe from
        """
        pass

    @abstractmethod
    def listen(self) -> Any:
        """
        Get message generator.

        Returns:
            Generator that yields messages as they arrive
        """
        pass

    @abstractmethod
    def get_message(self, timeout: float = 0.0) -> Optional[Dict]:
        """
        Get next message if available.

        Args:
            timeout: Timeout in seconds (0.0 for non-blocking)

        Returns:
            Message dict if available, None otherwise

        Message Format:
            {
                'type': 'message',
                'pattern': None,
                'channel': 'channel_name',
                'data': 'message_data'
            }
        """
        pass
