import redis
import json
import hashlib
from typing import Any, Optional
import logging
from core.config import settings
import pickle

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service for improving performance
    """
    
    def __init__(self):
        self.redis_client = None
        self.enabled = settings.enable_cache
        
        if self.enabled:
            try:
                # Parse Redis URL or use default
                redis_url = settings.redis_url or "redis://localhost:6379"
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We'll handle encoding/decoding
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, caching disabled: {e}")
                self.enabled = False
                self.redis_client = None
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from prefix and data"""
        # Create a stable hash of the data
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_digest = hashlib.md5(data_str.encode()).hexdigest()[:12]
        return f"{prefix}:{hash_digest}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Try to deserialize as JSON first, then pickle
                try:
                    return json.loads(value)
                except:
                    return pickle.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Try JSON serialization first, fall back to pickle
            try:
                serialized = json.dumps(value)
            except:
                serialized = pickle.dumps(value)
            
            ttl = ttl or settings.cache_ttl
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False
    
    async def get_query_result(self, query: str, user_id: Optional[str] = None) -> Optional[dict]:
        """Get cached query result"""
        cache_data = {
            'query': query.lower().strip(),
            'user_id': user_id or 'anonymous'
        }
        key = self._generate_key('query_result', cache_data)
        return await self.get(key)
    
    async def set_query_result(
        self, 
        query: str, 
        result: dict, 
        user_id: Optional[str] = None,
        ttl: int = 1800  # 30 minutes default
    ) -> bool:
        """Cache query result"""
        cache_data = {
            'query': query.lower().strip(),
            'user_id': user_id or 'anonymous'
        }
        key = self._generate_key('query_result', cache_data)
        return await self.set(key, result, ttl)
    
    async def get_search_terms(self, query: str) -> Optional[list]:
        """Get cached search term enhancements"""
        key = self._generate_key('search_terms', query.lower().strip())
        return await self.get(key)
    
    async def set_search_terms(self, query: str, terms: list, ttl: int = 3600) -> bool:
        """Cache search term enhancements"""
        key = self._generate_key('search_terms', query.lower().strip())
        return await self.set(key, terms, ttl)
    
    async def get_product_embeddings(self, product_ids: list) -> Optional[dict]:
        """Get cached product embeddings"""
        key = self._generate_key('embeddings', sorted(product_ids))
        return await self.get(key)
    
    async def set_product_embeddings(self, product_ids: list, embeddings: dict, ttl: int = 7200) -> bool:
        """Cache product embeddings"""
        key = self._generate_key('embeddings', sorted(product_ids))
        return await self.set(key, embeddings, ttl)
    
    async def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cache entries for a specific user"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Find and delete all keys for this user
            pattern = f"*:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error clearing user cache: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info('stats')
            return {
                "enabled": True,
                "keys": self.redis_client.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}