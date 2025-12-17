"""
Cache Management System
Long-term solution for cache lifecycle, expiration, and optimization
"""

import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = "data/cache"
CACHE_FILE = os.path.join(CACHE_DIR, "pubmed_results.json")
CACHE_EXPIRY_DAYS = 30  # Cache expires after 30 days
MAX_CACHE_SIZE_MB = 100  # Maximum cache size in MB
MAX_CACHE_ENTRIES = 50  # Maximum number of cached queries


class CacheManager:
    """
    Comprehensive cache management system with expiration, size limits, and optimization
    """
    
    def __init__(self, cache_file: str = CACHE_FILE, expiry_days: int = CACHE_EXPIRY_DAYS):
        self.cache_file = cache_file
        self.expiry_days = expiry_days
        self.cache_dir = os.path.dirname(cache_file)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_cache(self) -> Dict:
        """
        Load cache with validation and automatic cleanup
        
        Returns:
            Cache dictionary
        """
        if not os.path.exists(self.cache_file):
            return self._create_empty_cache()
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Validate structure
            if not isinstance(cache_data, dict):
                logger.warning("Invalid cache structure, creating new cache")
                return self._create_empty_cache()
            
            # Auto-cleanup expired entries
            cache_data = self._cleanup_expired_entries(cache_data)
            
            # Auto-cleanup if cache is too large
            cache_data = self._enforce_size_limits(cache_data)
            
            return cache_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Cache file corrupted: {e}")
            self._backup_corrupted_cache()
            return self._create_empty_cache()
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return self._create_empty_cache()
    
    def _create_empty_cache(self) -> Dict:
        """Create empty cache structure"""
        return {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'search_queries': {},
            'final_results': None,
            'metadata': {
                'total_queries': 0,
                'last_cleanup': datetime.now().isoformat()
            }
        }
    
    def _cleanup_expired_entries(self, cache: Dict) -> Dict:
        """
        Remove expired cache entries
        
        Args:
            cache: Cache dictionary
        
        Returns:
            Cleaned cache dictionary
        """
        if 'search_queries' not in cache:
            return cache
        
        expired_keys = []
        expiry_date = datetime.now() - timedelta(days=self.expiry_days)
        
        for key, entry in cache['search_queries'].items():
            timestamp_str = entry.get('timestamp', '')
            if timestamp_str:
                try:
                    entry_date = datetime.fromisoformat(timestamp_str)
                    if entry_date < expiry_date:
                        expired_keys.append(key)
                except (ValueError, TypeError):
                    # Invalid timestamp, mark for removal
                    expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del cache['search_queries'][key]
            logger.info(f"Removed expired cache entry: {key}")
        
        if expired_keys:
            cache['metadata']['last_cleanup'] = datetime.now().isoformat()
            cache['metadata']['total_queries'] = len(cache['search_queries'])
        
        return cache
    
    def _enforce_size_limits(self, cache: Dict) -> Dict:
        """
        Enforce cache size limits by removing oldest entries
        
        Args:
            cache: Cache dictionary
        
        Returns:
            Cache dictionary with size limits enforced
        """
        if 'search_queries' not in cache:
            return cache
        
        # Check file size
        try:
            file_size_mb = os.path.getsize(self.cache_file) / (1024 * 1024)
            if file_size_mb > MAX_CACHE_SIZE_MB:
                logger.info(f"Cache size ({file_size_mb:.2f} MB) exceeds limit, cleaning up...")
                cache = self._remove_oldest_entries(cache, keep_count=MAX_CACHE_ENTRIES)
        except Exception:
            pass
        
        # Check entry count
        if len(cache.get('search_queries', {})) > MAX_CACHE_ENTRIES:
            cache = self._remove_oldest_entries(cache, keep_count=MAX_CACHE_ENTRIES)
        
        return cache
    
    def _remove_oldest_entries(self, cache: Dict, keep_count: int) -> Dict:
        """
        Remove oldest cache entries, keeping only the most recent ones
        
        Args:
            cache: Cache dictionary
            keep_count: Number of entries to keep
        
        Returns:
            Cache dictionary with oldest entries removed
        """
        if 'search_queries' not in cache:
            return cache
        
        queries = cache['search_queries']
        
        # Sort by timestamp (newest first)
        sorted_entries = sorted(
            queries.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        # Keep only the most recent entries
        cache['search_queries'] = dict(sorted_entries[:keep_count])
        cache['metadata']['total_queries'] = len(cache['search_queries'])
        cache['metadata']['last_cleanup'] = datetime.now().isoformat()
        
        removed_count = len(sorted_entries) - keep_count
        if removed_count > 0:
            logger.info(f"Removed {removed_count} oldest cache entries")
        
        return cache
    
    def save_cache(self, cache: Dict) -> bool:
        """
        Save cache with atomic write operation
        
        Args:
            cache: Cache dictionary to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update metadata
            if 'metadata' not in cache:
                cache['metadata'] = {}
            cache['metadata']['total_queries'] = len(cache.get('search_queries', {}))
            cache['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Atomic write: write to temp file, then rename
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            if os.path.exists(temp_file):
                if os.path.exists(self.cache_file):
                    os.replace(temp_file, self.cache_file)
                else:
                    os.rename(temp_file, self.cache_file)
                return True
            return False
            
        except PermissionError as e:
            logger.error(f"Permission denied saving cache: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            # Clean up temp file
            temp_file = f"{self.cache_file}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return False
    
    def get_cached_results(self, cache_key: str) -> Optional[List[Dict]]:
        """
        Get cached results for a specific key
        
        Args:
            cache_key: Cache key (keyword + results_per_keyword + years_back)
        
        Returns:
            Cached results or None if not found/expired
        """
        cache = self.load_cache()
        queries = cache.get('search_queries', {})
        
        if cache_key not in queries:
            return None
        
        entry = queries[cache_key]
        
        # Check if expired
        timestamp_str = entry.get('timestamp', '')
        if timestamp_str:
            try:
                entry_date = datetime.fromisoformat(timestamp_str)
                if entry_date < datetime.now() - timedelta(days=self.expiry_days):
                    # Expired, remove it
                    del queries[cache_key]
                    self.save_cache(cache)
                    return None
            except (ValueError, TypeError):
                return None
        
        return entry.get('results', [])
    
    def save_query_results(self, cache_key: str, results: List[Dict]) -> bool:
        """
        Save query results to cache
        
        Args:
            cache_key: Cache key
            results: Results to cache
        
        Returns:
            True if successful
        """
        cache = self.load_cache()
        
        if 'search_queries' not in cache:
            cache['search_queries'] = {}
        
        cache['search_queries'][cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'count': len(results)
        }
        
        return self.save_cache(cache)
    
    def clear_all_cache(self) -> bool:
        """
        Clear all cached data
        
        Returns:
            True if successful
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def clear_query_cache(self, cache_key: str) -> bool:
        """
        Clear cached results for a specific query
        
        Args:
            cache_key: Cache key to clear
        
        Returns:
            True if successful
        """
        cache = self.load_cache()
        if cache_key in cache.get('search_queries', {}):
            del cache['search_queries'][cache_key]
            cache['metadata']['total_queries'] = len(cache.get('search_queries', {}))
            return self.save_cache(cache)
        return True
    
    def get_cache_info(self) -> Dict:
        """
        Get cache information (size, entries, etc.)
        
        Returns:
            Dictionary with cache information
        """
        info = {
            'exists': os.path.exists(self.cache_file),
            'file_size_mb': 0,
            'total_queries': 0,
            'expiry_days': self.expiry_days,
            'max_size_mb': MAX_CACHE_SIZE_MB,
            'max_entries': MAX_CACHE_ENTRIES
        }
        
        if info['exists']:
            try:
                info['file_size_mb'] = os.path.getsize(self.cache_file) / (1024 * 1024)
                cache = self.load_cache()
                info['total_queries'] = len(cache.get('search_queries', {}))
                info['last_cleanup'] = cache.get('metadata', {}).get('last_cleanup', 'Never')
            except Exception:
                pass
        
        return info
    
    def _backup_corrupted_cache(self):
        """Backup corrupted cache file"""
        if os.path.exists(self.cache_file):
            backup_file = f"{self.cache_file}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(self.cache_file, backup_file)
                logger.info(f"Corrupted cache backed up to {backup_file}")
            except Exception as e:
                logger.warning(f"Could not backup corrupted cache: {e}")

