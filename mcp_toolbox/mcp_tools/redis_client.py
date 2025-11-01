"""
Redis client for session caching and temporary data storage.

This module provides Redis connectivity and caching operations for the MCP toolbox.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
except ImportError:
    # Graceful degradation when Redis is not installed
    print("Warning: Redis dependencies are not installed. Install them with: pip install redis")
    redis = None
    Redis = None


class RedisManager:
    """Manages Redis connections and caching operations."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the Redis manager.

        Args:
            redis_url: Redis connection URL. If None, uses environment variables.
        """
        self.redis_url = redis_url or self._build_redis_url()
        self.redis_client: Optional[Redis] = None
        self.default_ttl = int(os.getenv('CACHE_TTL', '1800'))  # 30 minutes default

    def _build_redis_url(self) -> str:
        """Build Redis URL from environment variables."""
        if os.getenv('REDIS_URL'):
            return os.getenv('REDIS_URL')

        # Build from individual components
        host = os.getenv('REDIS_HOST', 'localhost')
        port = os.getenv('REDIS_PORT', '6379')
        db = os.getenv('REDIS_DB', '0')
        password = os.getenv('REDIS_PASSWORD', '')

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"

    async def initialize(self):
        """Initialize Redis connection."""
        if redis is None:
            raise ImportError("Redis dependencies are not installed")

        self.redis_client = redis.from_url(
            self.redis_url,
            decode_responses=True,
            health_check_interval=30
        )

        # Test connection
        await self.redis_client.ping()

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

    # Session caching operations
    async def cache_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache session data in Redis."""
        if not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            ttl = ttl or self.default_ttl

            # Add metadata
            cache_data = {
                **session_data,
                "_cached_at": datetime.utcnow().isoformat(),
                "_ttl": ttl
            }

            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            return True
        except Exception as e:
            print(f"Error caching session {session_id}: {e}")
            return False

    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data from Redis."""
        if not self.redis_client:
            return None

        try:
            key = f"session:{session_id}"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting cached session {session_id}: {e}")
            return None

    async def invalidate_session(self, session_id: str) -> bool:
        """Remove session from cache."""
        if not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Error invalidating session {session_id}: {e}")
            return False

    # Requirements caching
    async def cache_requirements(self, session_id: str, requirements: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache requirements for a session."""
        if not self.redis_client:
            return False

        try:
            key = f"requirements:{session_id}"
            ttl = ttl or self.default_ttl

            cache_data = {
                "requirements": requirements,
                "_cached_at": datetime.utcnow().isoformat(),
                "_count": len(requirements)
            }

            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            return True
        except Exception as e:
            print(f"Error caching requirements for session {session_id}: {e}")
            return False

    async def get_cached_requirements(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached requirements for a session."""
        if not self.redis_client:
            return None

        try:
            key = f"requirements:{session_id}"
            data = await self.redis_client.get(key)

            if data:
                cache_data = json.loads(data)
                return cache_data.get("requirements", [])
            return None
        except Exception as e:
            print(f"Error getting cached requirements for session {session_id}: {e}")
            return None

    # Test cases caching
    async def cache_test_cases(self, session_id: str, test_cases: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache test cases for a session."""
        if not self.redis_client:
            return False

        try:
            key = f"test_cases:{session_id}"
            ttl = ttl or self.default_ttl

            cache_data = {
                "test_cases": test_cases,
                "_cached_at": datetime.utcnow().isoformat(),
                "_count": len(test_cases)
            }

            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            return True
        except Exception as e:
            print(f"Error caching test cases for session {session_id}: {e}")
            return False

    async def get_cached_test_cases(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached test cases for a session."""
        if not self.redis_client:
            return None

        try:
            key = f"test_cases:{session_id}"
            data = await self.redis_client.get(key)

            if data:
                cache_data = json.loads(data)
                return cache_data.get("test_cases", [])
            return None
        except Exception as e:
            print(f"Error getting cached test cases for session {session_id}: {e}")
            return None

    # General purpose caching
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis."""
        if not self.redis_client:
            return False

        try:
            ttl = ttl or self.default_ttl

            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)

            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            print(f"Error setting key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)

            if value is None:
                return None

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Error getting key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            print(f"Error checking key {key}: {e}")
            return False

    # Session state management
    async def set_session_state(self, session_id: str, state: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Set session state with optional data."""
        state_data = {
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }

        key = f"session_state:{session_id}"
        return await self.set(key, state_data)

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state."""
        key = f"session_state:{session_id}"
        return await self.get(key)

    # Agent workflow tracking
    async def track_workflow_step(self, session_id: str, step: str, result: Dict[str, Any]) -> bool:
        """Track workflow step execution."""
        workflow_data = {
            "step": step,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to workflow history
        key = f"workflow_history:{session_id}"

        try:
            if not self.redis_client:
                return False

            # Get existing history
            existing_data = await self.redis_client.get(key)
            if existing_data:
                history = json.loads(existing_data)
            else:
                history = {"steps": []}

            # Add new step
            history["steps"].append(workflow_data)
            history["last_updated"] = datetime.utcnow().isoformat()

            # Save back to Redis
            await self.redis_client.setex(
                key,
                self.default_ttl,
                json.dumps(history, default=str)
            )
            return True
        except Exception as e:
            print(f"Error tracking workflow step for session {session_id}: {e}")
            return False

    async def get_workflow_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution history for a session."""
        key = f"workflow_history:{session_id}"
        return await self.get(key)

    # Cache management
    async def clear_session_cache(self, session_id: str) -> int:
        """Clear all cache entries for a session."""
        if not self.redis_client:
            return 0

        try:
            keys_to_delete = [
                f"session:{session_id}",
                f"requirements:{session_id}",
                f"test_cases:{session_id}",
                f"session_state:{session_id}",
                f"workflow_history:{session_id}"
            ]

            deleted_count = 0
            for key in keys_to_delete:
                if await self.redis_client.delete(key):
                    deleted_count += 1

            return deleted_count
        except Exception as e:
            print(f"Error clearing session cache for {session_id}: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {}

        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "cache_hit_ratio": (
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                )
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}


# Global Redis manager instance
redis_manager = RedisManager()