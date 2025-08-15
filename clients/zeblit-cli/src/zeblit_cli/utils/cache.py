"""
Offline caching utilities for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial offline caching implementation.
"""

import json
import os
import time
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

from rich.console import Console

console = Console()


class CacheManager:
    """Manager for offline caching of API responses."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files (defaults to ~/.zeblit/cache)
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.zeblit/cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes default TTL
        self.max_cache_size = 50 * 1024 * 1024  # 50MB max cache size
        
        # Cache stats
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Create safe filename from key
        safe_key = key.replace("/", "_").replace(":", "_").replace("?", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def _is_expired(self, cache_data: Dict) -> bool:
        """Check if cache entry is expired."""
        if "expires_at" not in cache_data:
            return True
        
        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        return datetime.now() > expires_at
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached value or default
        """
        try:
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                self._stats["misses"] += 1
                return default
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check expiration
            if self._is_expired(cache_data):
                self._stats["misses"] += 1
                self._remove_cache_file(cache_path)
                return default
            
            self._stats["hits"] += 1
            return cache_data.get("data", default)
            
        except (json.JSONDecodeError, IOError, KeyError):
            self._stats["misses"] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successfully cached
        """
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            cache_data = {
                "data": value,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl
            }
            
            cache_path = self._get_cache_path(key)
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            # Check cache size and cleanup if needed
            self._cleanup_if_needed()
            
            return True
            
        except (IOError, TypeError):
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted successfully
        """
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
        except IOError:
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if cleared successfully
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            self._stats = {"hits": 0, "misses": 0, "evictions": 0}
            return True
            
        except IOError:
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    if self._is_expired(cache_data):
                        cache_file.unlink()
                        removed += 1
                        
                except (json.JSONDecodeError, IOError):
                    # Remove corrupted cache files
                    cache_file.unlink()
                    removed += 1
            
            self._stats["evictions"] += removed
            return removed
            
        except Exception:
            return removed
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size
        except Exception:
            pass
        
        return total_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_size = self.get_cache_size()
        file_count = len(list(self.cache_dir.glob("*.json")))
        
        hit_rate = 0
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            hit_rate = (self._stats["hits"] / total_requests) * 100
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": hit_rate,
            "cache_size_bytes": cache_size,
            "cache_size_human": self._format_bytes(cache_size),
            "file_count": file_count,
            "cache_dir": str(self.cache_dir)
        }
    
    def _cleanup_if_needed(self):
        """Cleanup cache if it exceeds size limit."""
        cache_size = self.get_cache_size()
        
        if cache_size > self.max_cache_size:
            # Remove oldest files first
            cache_files = list(self.cache_dir.glob("*.json"))
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove oldest 25% of files
            remove_count = max(1, len(cache_files) // 4)
            
            for cache_file in cache_files[:remove_count]:
                self._remove_cache_file(cache_file)
                self._stats["evictions"] += 1
    
    def _remove_cache_file(self, cache_path: Path):
        """Safely remove a cache file."""
        try:
            if cache_path.exists():
                cache_path.unlink()
        except IOError:
            pass
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} TB"


class APICache:
    """High-level cache for API responses."""
    
    def __init__(self):
        """Initialize API cache."""
        self.cache = CacheManager()
        
        # Different TTLs for different types of data
        self.ttls = {
            "projects": 300,     # 5 minutes
            "chat_history": 60,  # 1 minute
            "file_tree": 120,    # 2 minutes
            "container_status": 30,  # 30 seconds
            "user_info": 600,    # 10 minutes
        }
    
    def cache_projects(self, user_id: str, projects: List[Dict]) -> bool:
        """Cache user's projects."""
        key = f"projects:{user_id}"
        return self.cache.set(key, projects, self.ttls["projects"])
    
    def get_cached_projects(self, user_id: str) -> Optional[List[Dict]]:
        """Get cached projects."""
        key = f"projects:{user_id}"
        return self.cache.get(key)
    
    def cache_chat_history(self, project_id: str, history: List[Dict]) -> bool:
        """Cache chat history."""
        key = f"chat_history:{project_id}"
        return self.cache.set(key, history, self.ttls["chat_history"])
    
    def get_cached_chat_history(self, project_id: str) -> Optional[List[Dict]]:
        """Get cached chat history."""
        key = f"chat_history:{project_id}"
        return self.cache.get(key)
    
    def cache_file_tree(self, project_id: str, file_tree: Dict) -> bool:
        """Cache file tree."""
        key = f"file_tree:{project_id}"
        return self.cache.set(key, file_tree, self.ttls["file_tree"])
    
    def get_cached_file_tree(self, project_id: str) -> Optional[Dict]:
        """Get cached file tree."""
        key = f"file_tree:{project_id}"
        return self.cache.get(key)
    
    def cache_container_status(self, project_id: str, status: Dict) -> bool:
        """Cache container status."""
        key = f"container_status:{project_id}"
        return self.cache.set(key, status, self.ttls["container_status"])
    
    def get_cached_container_status(self, project_id: str) -> Optional[Dict]:
        """Get cached container status."""
        key = f"container_status:{project_id}"
        return self.cache.get(key)
    
    def cache_user_info(self, user_id: str, user_info: Dict) -> bool:
        """Cache user info."""
        key = f"user_info:{user_id}"
        return self.cache.set(key, user_info, self.ttls["user_info"])
    
    def get_cached_user_info(self, user_id: str) -> Optional[Dict]:
        """Get cached user info."""
        key = f"user_info:{user_id}"
        return self.cache.get(key)
    
    def invalidate_project_cache(self, project_id: str):
        """Invalidate all cache entries for a project."""
        keys_to_delete = [
            f"chat_history:{project_id}",
            f"file_tree:{project_id}",
            f"container_status:{project_id}"
        ]
        
        for key in keys_to_delete:
            self.cache.delete(key)
    
    def show_cache_info(self):
        """Show cache information."""
        stats = self.cache.get_stats()
        
        console.print("\n[bold]Cache Statistics[/bold]")
        console.print(f"📊 Hit rate: {stats['hit_rate']:.1f}%")
        console.print(f"📈 Hits: {stats['hits']}, Misses: {stats['misses']}")
        console.print(f"🗑️  Evictions: {stats['evictions']}")
        console.print(f"💾 Cache size: {stats['cache_size_human']} ({stats['file_count']} files)")
        console.print(f"📁 Cache directory: {stats['cache_dir']}")
    
    def cleanup(self):
        """Cleanup expired cache entries."""
        removed = self.cache.cleanup_expired()
        if removed > 0:
            console.print(f"🧹 Cleaned up {removed} expired cache entries")


# Global API cache instance
api_cache = APICache()


def cached_api_call(cache_key: str, api_call, ttl: Optional[int] = None):
    """
    Decorator-like function for caching API calls.
    
    Args:
        cache_key: Key for caching
        api_call: Async function to call
        ttl: Time to live for cache entry
        
    Returns:
        Cached result or fresh API call result
    """
    cache_manager = CacheManager()
    
    # Try to get from cache first
    cached_result = cache_manager.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # If not cached, make API call and cache result
    async def make_call():
        result = await api_call()
        cache_manager.set(cache_key, result, ttl)
        return result
    
    return make_call()
