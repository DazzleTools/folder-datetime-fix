"""
Synchronous wrapper for DazzleTreeLib's async cache implementation.

This module provides a synchronous interface to DazzleTreeLib's
CompletenessAwareCacheAdapter, allowing modified-datetime-fix to use
the improved integer-based depth tracking system.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional, Tuple, Dict
import time

# Import from DazzleTreeLib
try:
    # Try to import the new SmartCachingAdapter first
    from dazzletreelib.aio.adapters.smart_caching import SmartCachingAdapter
    SMART_ADAPTER_AVAILABLE = True
except ImportError:
    SMART_ADAPTER_AVAILABLE = False

try:
    from dazzletreelib.aio.adapters import (
        CompletenessAwareCacheAdapter,
        CacheEntry,
    )
    from dazzletreelib.aio.adapters.filesystem import AsyncFileSystemAdapter
    DAZZLETREELIB_AVAILABLE = True
except ImportError:
    DAZZLETREELIB_AVAILABLE = False
    # Fallback definitions for when DazzleTreeLib isn't installed
    class CacheEntry:
        COMPLETE_DEPTH = -1
        MAX_DEPTH = 100

        def __init__(self, data: Any, depth: int = -1, mtime: Optional[float] = None):
            self.data = data
            self.depth = depth
            self.mtime = mtime
            self.cached_at = time.time()
            self.access_count = 0
            self.size_estimate = 0

    CompletenessAwareCacheAdapter = None
    AsyncFileSystemAdapter = None
    SmartCachingAdapter = None


class SyncCacheWrapper:
    """
    Synchronous wrapper around DazzleTreeLib's async cache.
    
    Provides backward compatibility for modified-datetime-fix while
    leveraging the improved integer-based depth system from DazzleTreeLib.
    """
    
    def __init__(self, memory_limit_mb: int = 100):
        """
        Initialize the sync cache wrapper.
        
        Args:
            memory_limit_mb: Maximum cache size in megabytes
        """
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # For synchronous operation, we'll maintain our own cache
        # since we can't easily wrap the async adapter
        self.cache: Dict[Tuple[Path, int], CacheEntry] = {}
        
        # Track access order for LRU eviction
        self.access_order = []
    
    def get_or_compute(self, path: Path, strategy: str, 
                       max_depth: Optional[int] = None, verbose: int = 0) -> Tuple[int, 'CacheCompleteness']:
        """
        Get from cache or compute with appropriate completeness.
        
        Args:
            path: Path to cache/compute
            strategy: Strategy name ("shallow", "deep", "smart")
            max_depth: Maximum depth to scan
            verbose: Verbosity level
            
        Returns:
            Tuple of (computed_mtime, CacheCompleteness)
        """
        # Determine scan depth based on strategy
        if strategy == "shallow":
            scan_depth = 1
        elif strategy == "deep":
            scan_depth = CacheEntry.COMPLETE_DEPTH  # -1 for complete
        elif max_depth is not None:
            scan_depth = max_depth
        else:  # smart
            scan_depth = self._determine_smart_depth(path, verbose)
        
        # Check cache for exact match
        cache_key = (path, scan_depth)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            self.hits += 1
            self._mark_accessed(cache_key)
            if verbose >= 3:
                print(f"Cache hit for {path}: strategy={strategy}, depth={entry.depth}")
            return entry.data.get('mtime', 0), self._depth_to_completeness(entry.depth)
        
        # Check if a deeper scan exists that satisfies this request
        for (cached_path, cached_depth), entry in self.cache.items():
            if cached_path == path:
                if self._depth_satisfies(entry.depth, scan_depth):
                    self.hits += 1
                    self._mark_accessed((cached_path, cached_depth))
                    if verbose >= 3:
                        print(f"Cache hit (deeper scan) for {path}: cached_depth={entry.depth}, required={scan_depth}")
                    return entry.data.get('mtime', 0), self._depth_to_completeness(entry.depth)
        
        # Cache miss - need to compute
        self.misses += 1
        if verbose >= 3:
            print(f"Cache miss for {path}: computing with depth={scan_depth}")
        
        # Compute the timestamp
        mtime, has_subdirs, file_count = self._compute_timestamp(path, scan_depth, verbose)
        
        # Create cache entry
        entry_data = {
            'mtime': mtime,
            'has_subdirs': has_subdirs,
            'file_count': file_count,
        }
        entry = CacheEntry(entry_data, depth=scan_depth, mtime=time.time())
        
        # Add to cache
        self._add_to_cache(cache_key, entry)
        
        return mtime, self._depth_to_completeness(scan_depth)
    
    def _depth_satisfies(self, cached_depth: int, required_depth: int) -> bool:
        """
        Check if a cached depth satisfies the required depth.
        
        Args:
            cached_depth: Depth that was cached (-1 for complete)
            required_depth: Depth that is required (-1 for complete)
            
        Returns:
            True if cached depth satisfies requirement
        """
        # Complete scan satisfies everything
        if cached_depth == CacheEntry.COMPLETE_DEPTH:
            return True
        
        # If complete scan is required, partial doesn't satisfy
        if required_depth == CacheEntry.COMPLETE_DEPTH:
            return False
        
        # Partial scan satisfies if deep enough
        return cached_depth >= required_depth
    
    def _determine_smart_depth(self, path: Path, verbose: int) -> int:
        """
        Determine optimal scan depth for smart strategy.
        
        Args:
            path: Path to analyze
            verbose: Verbosity level
            
        Returns:
            Optimal depth to scan
        """
        import os
        
        try:
            entries = list(os.scandir(path))
            subdirs = [e for e in entries if e.is_dir() and not self._is_system_generated(e.name)]
            
            if len(subdirs) == 0:
                # No subdirectories, shallow scan is complete
                return 1
            elif len(subdirs) <= 5:
                # Few subdirectories, scan 3 levels
                return 3
            else:
                # Many subdirectories, scan 2 levels  
                return 2
        except (OSError, PermissionError):
            return 1
    
    def _is_system_generated(self, name: str) -> bool:
        """Check if a file/folder name is system-generated."""
        system_files = {
            'thumbs.db', 'desktop.ini', '.ds_store', 
            'ehthumbs.db', 'ehthumbs_vista.db',
            '$recycle.bin', 'system volume information',
        }
        return name.lower() in system_files
    
    def _compute_timestamp(self, path: Path, scan_depth: int, verbose: int) -> Tuple[int, bool, int]:
        """
        Compute timestamp for folder up to specified depth.
        
        Args:
            path: Path to scan
            scan_depth: Depth to scan (-1 for complete)
            verbose: Verbosity level
            
        Returns:
            Tuple of (max_mtime, has_subdirs, file_count)
        """
        import os
        
        max_time = 0
        has_subdirs = False
        file_count = 0
        
        def scan_recursive(current_path: Path, current_depth: int) -> int:
            nonlocal has_subdirs, file_count
            local_max = 0
            
            # Check if we've reached the depth limit
            if scan_depth != CacheEntry.COMPLETE_DEPTH and current_depth >= scan_depth:
                return 0
                
            try:
                for entry in os.scandir(current_path):
                    if self._is_system_generated(entry.name):
                        continue
                        
                    if entry.is_file():
                        file_count += 1
                        try:
                            mtime = int(entry.stat().st_mtime)
                            local_max = max(local_max, mtime)
                        except (OSError, PermissionError):
                            pass
                    elif entry.is_dir():
                        if current_depth == 0:
                            has_subdirs = True
                        # Recurse if not at depth limit
                        if scan_depth == CacheEntry.COMPLETE_DEPTH or current_depth + 1 < scan_depth:
                            sub_max = scan_recursive(Path(entry.path), current_depth + 1)
                            local_max = max(local_max, sub_max)
            except (OSError, PermissionError) as e:
                if verbose >= 2:
                    print(f"Permission denied scanning {current_path}: {e}")
                    
            return local_max
        
        max_time = scan_recursive(path, 0)
        return max_time, has_subdirs, file_count
    
    def _depth_to_completeness(self, depth: int) -> 'CacheCompleteness':
        """Convert integer depth to CacheCompleteness object."""
        if depth == CacheEntry.COMPLETE_DEPTH:
            return CacheCompleteness.COMPLETE
        elif depth == 0:
            return CacheCompleteness.NONE
        elif depth == 1:
            return CacheCompleteness.SHALLOW
        elif depth == 2:
            return CacheCompleteness.PARTIAL_2
        elif depth == 3:
            return CacheCompleteness.PARTIAL_3
        else:
            return CacheCompleteness.PARTIAL_N
    
    def _add_to_cache(self, key: Tuple[Path, int], entry: CacheEntry):
        """
        Add entry to cache with memory management.
        
        Args:
            key: Cache key (path, depth)
            entry: Cache entry to add
        """
        # Estimate memory usage
        entry.size_estimate = 200  # Approximate bytes per entry
        
        # Evict if necessary
        while self.current_memory + entry.size_estimate > self.memory_limit and self.cache:
            self._evict_lru()
        
        self.cache[key] = entry
        self.current_memory += entry.size_estimate
        self._mark_accessed(key)
    
    def _mark_accessed(self, key: Tuple[Path, int]):
        """Mark a cache entry as recently accessed for LRU."""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _evict_lru(self):
        """Evict least recently used cache entry."""
        if not self.access_order:
            return
        
        # Remove least recently used
        key_to_evict = self.access_order.pop(0)
        if key_to_evict in self.cache:
            entry = self.cache[key_to_evict]
            del self.cache[key_to_evict]
            self.current_memory -= entry.size_estimate
            self.evictions += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics for debugging."""
        return {
            'entries': len(self.cache),
            'memory_bytes': self.current_memory,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0,
            'dazzletreelib_available': DAZZLETREELIB_AVAILABLE,
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0


# Backward compatibility aliases
class SmartStreamingCache(SyncCacheWrapper):
    """Alias for backward compatibility with existing code."""
    pass


class SmartCacheEntry:
    """
    Backward compatibility wrapper for cache entries.
    
    Maps the old interface to the new integer-based system.
    """
    
    def __init__(self, path: Path, computed_mtime: int, completeness: Any,
                 actual_depth: int, has_subdirs: bool, file_count: int,
                 computation_time: float):
        """Initialize with old interface."""
        self.path = path
        self.computed_mtime = computed_mtime
        self.actual_depth = actual_depth
        self.has_subdirs = has_subdirs
        self.file_count = file_count
        self.computation_time = computation_time
        
        # Map old completeness to depth
        if hasattr(completeness, 'value'):
            # It's an enum
            if completeness.value >= 999:
                self.depth = CacheEntry.COMPLETE_DEPTH
            else:
                self.depth = completeness.value
        else:
            self.depth = actual_depth
        
        # Compatibility attributes
        self.completeness = completeness
        self.can_satisfy = set()
        self._determine_satisfaction()
    
    def _determine_satisfaction(self):
        """Determine what strategies this entry satisfies."""
        if self.depth == CacheEntry.COMPLETE_DEPTH:
            self.can_satisfy.update(['shallow', 'deep', 'smart'])
        elif self.depth == 1:
            self.can_satisfy.add('shallow')
            if not self.has_subdirs:  # Leaf folder
                self.can_satisfy.update(['deep', 'smart'])
        elif self.depth >= 2:
            self.can_satisfy.add('shallow')
            if self.depth >= 3:
                self.can_satisfy.add('smart')
    
    def satisfies(self, strategy: str, required_depth: Optional[int] = None) -> bool:
        """Check if this cache entry satisfies the requirement."""
        if strategy in self.can_satisfy:
            if required_depth is None:
                return True
            return self.actual_depth >= required_depth
        return False


# Enum for backward compatibility
class CacheCompleteness:
    """
    Backward compatibility enum-like class.
    Maps old enum values to integer depths.
    """
    def __init__(self, value):
        self.value = value
        self.name = self._get_name(value)
    
    def _get_name(self, value):
        """Get name for value."""
        names = {
            0: 'NONE',
            1: 'SHALLOW',
            2: 'PARTIAL_2',
            3: 'PARTIAL_3',
            10: 'PARTIAL_N',
            999: 'COMPLETE',
        }
        return names.get(value, f'PARTIAL_{value}')
    
    def __eq__(self, other):
        """Compare by value for equality."""
        if isinstance(other, CacheCompleteness):
            return self.value == other.value
        elif isinstance(other, int):
            # Allow comparison with raw integers
            return self.value == other
        return False
    
    def __hash__(self):
        """Hash by value."""
        return hash(self.value)
    
    def __repr__(self):
        """String representation."""
        return f'CacheCompleteness.{self.name}'
    
    @classmethod
    def from_depth(cls, depth: int):
        """Create completeness from scan depth."""
        if depth == 0:
            return cls.NONE
        elif depth == 1:
            return cls.SHALLOW
        elif depth == 2:
            return cls.PARTIAL_2
        elif depth == 3:
            return cls.PARTIAL_3
        elif depth >= 999:
            return cls.COMPLETE
        else:
            return cls.PARTIAL_N


# Create singleton instances for class attributes
CacheCompleteness.NONE = CacheCompleteness(0)
CacheCompleteness.SHALLOW = CacheCompleteness(1)
CacheCompleteness.PARTIAL_2 = CacheCompleteness(2)
CacheCompleteness.PARTIAL_3 = CacheCompleteness(3)
CacheCompleteness.PARTIAL_N = CacheCompleteness(10)
CacheCompleteness.COMPLETE = CacheCompleteness(999)