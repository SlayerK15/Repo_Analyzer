"""
Caching Infrastructure for the Technology Extraction System.

This module provides functionality for caching analysis results
to improve performance and reduce API costs.
"""
import hashlib
import json
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import redis

from tech_extraction.config import settings

logger = logging.getLogger(__name__)


class CacheBase:
    """Abstract base class for cache implementations."""
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        raise NotImplementedError
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError


class FileCache(CacheBase):
    """File-based cache implementation."""
    
    def __init__(self, cache_dir: str):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different cache types
        self.file_cache_dir = self.cache_dir / "files"
        self.analysis_cache_dir = self.cache_dir / "analysis"
        self.ai_cache_dir = self.cache_dir / "ai"
        
        self.file_cache_dir.mkdir(exist_ok=True)
        self.analysis_cache_dir.mkdir(exist_ok=True)
        self.ai_cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        # Use a subset of the hash to avoid filename length limits
        hash_key = hashlib.md5(key.encode()).hexdigest()[:16]
        
        # Determine the appropriate subdirectory
        if key.startswith("file:"):
            return self.file_cache_dir / f"{hash_key}.cache"
        elif key.startswith("ai:"):
            return self.ai_cache_dir / f"{hash_key}.cache"
        else:
            return self.analysis_cache_dir / f"{hash_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the file cache."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "rb") as f:
                # Read metadata (TTL, timestamp)
                metadata = pickle.load(f)
                
                # Check if expired
                if metadata.get("ttl"):
                    creation_time = metadata.get("timestamp", 0)
                    if time.time() > creation_time + metadata["ttl"]:
                        # Expired
                        self.delete(key)
                        return None
                
                # Read the actual data
                value = pickle.load(f)
                
                logger.debug(f"Cache hit for key {key}")
                return value
                
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the file cache."""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, "wb") as f:
                # Write metadata (TTL, timestamp)
                metadata = {
                    "ttl": ttl,
                    "timestamp": time.time(),
                    "key": key,
                }
                pickle.dump(metadata, f)
                
                # Write the actual data
                pickle.dump(value, f)
            
            logger.debug(f"Cached value for key {key}")
            return True
                
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the file cache."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return False
        
        try:
            cache_path.unlink()
            logger.debug(f"Deleted cache for key {key}")
            return True
                
        except Exception as e:
            logger.warning(f"Error deleting cache for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the file cache."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, "rb") as f:
                # Read metadata (TTL, timestamp)
                metadata = pickle.load(f)
                
                # Check if expired
                if metadata.get("ttl"):
                    creation_time = metadata.get("timestamp", 0)
                    if time.time() > creation_time + metadata["ttl"]:
                        # Expired
                        self.delete(key)
                        return False
                
                return True
                
        except Exception as e:
            logger.warning(f"Error checking cache for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all file cache entries."""
        try:
            # Delete all cache files
            for cache_dir in [self.file_cache_dir, self.analysis_cache_dir, self.ai_cache_dir]:
                for cache_file in cache_dir.glob("*.cache"):
                    cache_file.unlink()
            
            logger.info("Cleared file cache")
            return True
                
        except Exception as e:
            logger.warning(f"Error clearing file cache: {e}")
            return False


class RedisCache(CacheBase):
    """Redis-based cache implementation."""
    
    def __init__(self, redis_url: str):
        """
        Initialize the Redis cache.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        
        # Set a prefix for keys to avoid collisions
        self.key_prefix = "tech_extraction:"
        
        # Connect to Redis
        try:
            self.client = redis.from_url(redis_url)
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise
    
    def _prefix_key(self, key: str) -> str:
        """
        Add the key prefix.
        
        Args:
            key: Original key
            
        Returns:
            Prefixed key
        """
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the Redis cache."""
        prefixed_key = self._prefix_key(key)
        
        try:
            value = self.client.get(prefixed_key)
            
            if value is None:
                return None
            
            # Deserialize
            deserialized = pickle.loads(value)
            
            logger.debug(f"Cache hit for key {key}")
            return deserialized
                
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the Redis cache."""
        prefixed_key = self._prefix_key(key)
        
        try:
            # Serialize
            serialized = pickle.dumps(value)
            
            if ttl:
                self.client.setex(prefixed_key, ttl, serialized)
            else:
                self.client.set(prefixed_key, serialized)
            
            logger.debug(f"Cached value for key {key}")
            return True
                
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the Redis cache."""
        prefixed_key = self._prefix_key(key)
        
        try:
            result = self.client.delete(prefixed_key)
            success = result > 0
            
            if success:
                logger.debug(f"Deleted cache for key {key}")
            
            return success
                
        except Exception as e:
            logger.warning(f"Error deleting cache for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the Redis cache."""
        prefixed_key = self._prefix_key(key)
        
        try:
            return bool(self.client.exists(prefixed_key))
                
        except Exception as e:
            logger.warning(f"Error checking cache for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all Redis cache entries with our prefix."""
        try:
            # Find all keys with our prefix
            pattern = f"{self.key_prefix}*"
            keys = self.client.keys(pattern)
            
            if keys:
                # Delete all matching keys
                self.client.delete(*keys)
            
            logger.info(f"Cleared {len(keys)} keys from Redis cache")
            return True
                
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")
            return False


class MultiLevelCache:
    """
    Multi-level cache implementation.
    
    Provides a layered caching approach with multiple cache backends
    for improved performance and reliability.
    """
    
    def __init__(self):
        """Initialize the multi-level cache."""
        self.cache_levels = []
        
        # Set up caches based on configuration
        
        # Level 1: Memory cache (always used)
        self.memory_cache = {}
        self.cache_levels.append(("memory", self.memory_cache))
        
        # Level 2: File cache
        cache_dir = os.path.join(os.path.expanduser("~"), ".tech_extraction", "cache")
        self.file_cache = FileCache(cache_dir)
        self.cache_levels.append(("file", self.file_cache))
        
        # Level 3: Redis cache (if configured)
        if settings.redis.redis_url:
            try:
                self.redis_cache = RedisCache(settings.redis.redis_url)
                self.cache_levels.append(("redis", self.redis_cache))
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self.redis_cache = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache, trying each level.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Try memory cache first
        if key in self.memory_cache:
            logger.debug(f"Memory cache hit for key {key}")
            return self.memory_cache[key]
        
        # Try file cache
        file_result = self.file_cache.get(key)
        if file_result is not None:
            # Cache in memory for faster access next time
            self.memory_cache[key] = file_result
            return file_result
        
        # Try Redis cache if available
        if hasattr(self, "redis_cache") and self.redis_cache:
            redis_result = self.redis_cache.get(key)
            if redis_result is not None:
                # Cache in lower levels for faster access next time
                self.memory_cache[key] = redis_result
                self.file_cache.set(key, redis_result)
                return redis_result
        
        # Not found in any cache
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in all cache levels.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            True if successful at any level, False otherwise
        """
        success = False
        
        # Set in memory cache
        try:
            self.memory_cache[key] = value
            success = True
        except Exception as e:
            logger.warning(f"Error setting memory cache for key {key}: {e}")
        
        # Set in file cache
        file_success = self.file_cache.set(key, value, ttl)
        success = success or file_success
        
        # Set in Redis cache if available
        if hasattr(self, "redis_cache") and self.redis_cache:
            redis_success = self.redis_cache.set(key, value, ttl)
            success = success or redis_success
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from all cache levels.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful at any level, False otherwise
        """
        success = False
        
        # Delete from memory cache
        if key in self.memory_cache:
            try:
                del self.memory_cache[key]
                success = True
            except Exception as e:
                logger.warning(f"Error deleting from memory cache for key {key}: {e}")
        
        # Delete from file cache
        file_success = self.file_cache.delete(key)
        success = success or file_success
        
        # Delete from Redis cache if available
        if hasattr(self, "redis_cache") and self.redis_cache:
            redis_success = self.redis_cache.delete(key)
            success = success or redis_success
        
        return success
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in any cache level.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        # Check memory cache first
        if key in self.memory_cache:
            return True
        
        # Check file cache
        if self.file_cache.exists(key):
            return True
        
        # Check Redis cache if available
        if hasattr(self, "redis_cache") and self.redis_cache:
            if self.redis_cache.exists(key):
                return True
        
        return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries from all levels.
        
        Returns:
            True if successful at any level, False otherwise
        """
        success = False
        
        # Clear memory cache
        try:
            self.memory_cache.clear()
            success = True
        except Exception as e:
            logger.warning(f"Error clearing memory cache: {e}")
        
        # Clear file cache
        file_success = self.file_cache.clear()
        success = success or file_success
        
        # Clear Redis cache if available
        if hasattr(self, "redis_cache") and self.redis_cache:
            redis_success = self.redis_cache.clear()
            success = success or redis_success
        
        return success
    
    def generate_file_hash_key(self, file_path: str, file_size: int, mtime: float) -> str:
        """
        Generate a cache key for a file based on its path, size, and modification time.
        
        Args:
            file_path: Path to the file
            file_size: File size in bytes
            mtime: File modification time
            
        Returns:
            Cache key for the file
        """
        key_parts = [
            "file:",
            file_path,
            str(file_size),
            str(mtime)
        ]
        
        return ":".join(key_parts)
    
    def generate_analysis_key(self, analysis_type: str, files_hash: str, parameters: Dict) -> str:
        """
        Generate a cache key for analysis results.
        
        Args:
            analysis_type: Type of analysis
            files_hash: Hash of the files being analyzed
            parameters: Analysis parameters
            
        Returns:
            Cache key for the analysis results
        """
        # Sort parameters for consistent keys
        sorted_params = json.dumps(parameters, sort_keys=True)
        
        key_parts = [
            "analysis:",
            analysis_type,
            files_hash,
            sorted_params
        ]
        
        return ":".join(key_parts)
    
    def generate_ai_key(self, prompt: str, model: str) -> str:
        """
        Generate a cache key for AI results.
        
        Args:
            prompt: AI prompt
            model: AI model name
            
        Returns:
            Cache key for the AI results
        """
        # Hash the prompt to keep the key size reasonable
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        key_parts = [
            "ai:",
            model,
            prompt_hash
        ]
        
        return ":".join(key_parts)


# Create a global instance
cache = MultiLevelCache()