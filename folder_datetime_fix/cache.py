# folder_datetime_fix/cache.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple, List
from pathlib import Path
import time
import os
from .system_files import is_system_generated


class CacheCompleteness(Enum):
    """Indicates how thoroughly a folder has been scanned."""
    NONE = 0           # Not scanned
    SHALLOW = 1        # Immediate children only (depth=1) 
    PARTIAL_2 = 2      # 2 levels deep
    PARTIAL_3 = 3      # 3 levels deep
    PARTIAL_N = 10     # N levels deep (use value for actual depth)
    COMPLETE = 999     # Fully recursive to all leaves
    
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
            return cls.PARTIAL_N  # Store actual depth separately


@dataclass
class SmartCacheEntry:
    """
    Unified cache entry with progressive enhancement.
    """
    path: Path
    # Core data
    computed_mtime: int
    completeness: CacheCompleteness
    actual_depth: int  # Actual depth scanned
    
    # Metadata for smart decisions
    has_subdirs: bool
    file_count: int
    computation_time: float
    
    # Strategy tracking
    can_satisfy: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Determine what strategies this entry satisfies."""
        self.can_satisfy = set()
        
        if self.completeness == CacheCompleteness.COMPLETE:
            self.can_satisfy.update(['shallow', 'deep', 'smart'])
        elif self.completeness == CacheCompleteness.SHALLOW:
            self.can_satisfy.add('shallow')
            if not self.has_subdirs:  # Shallow is complete for leaf folders
                self.can_satisfy.update(['deep', 'smart'])
        elif self.completeness.value >= 2:  # Partial scans
            self.can_satisfy.add('shallow')
            # Can satisfy smart if we went deep enough
            if self.actual_depth >= 3:
                self.can_satisfy.add('smart')
    
    def satisfies(self, strategy: str, required_depth: int = None) -> bool:
        """Check if this cache entry satisfies the requirement."""
        if strategy in self.can_satisfy:
            if required_depth is None:
                return True
            return self.actual_depth >= required_depth
        return False


class SmartStreamingCache:
    """
    Main cache implementation with completeness tracking.
    """
    
    def __init__(self, memory_limit_mb: int = 100):
        self.cache: Dict[Path, SmartCacheEntry] = {}
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
    def get_or_compute(self, path: Path, strategy: str, 
                       max_depth: int = None, verbose: int = 0) -> Tuple[int, CacheCompleteness]:
        """
        Get from cache or compute with appropriate completeness.
        """
        # Check cache
        if path in self.cache:
            entry = self.cache[path]
            if entry.satisfies(strategy, max_depth):
                self.hits += 1
                if verbose >= 3:
                    print(f"Cache hit for {path}: strategy={strategy}, completeness={entry.completeness.name}")
                return entry.computed_mtime, entry.completeness
        
        self.misses += 1
        
        # Determine scan depth based on strategy
        if strategy == "shallow":
            scan_depth = 1
        elif strategy == "deep":
            scan_depth = 999  # Complete scan
        elif max_depth:
            scan_depth = max_depth
        else:  # smart
            scan_depth = self._determine_smart_depth(path, verbose)
        
        if verbose >= 3:
            print(f"Cache miss for {path}: computing with depth={scan_depth}")
        
        # Compute
        mtime, has_subdirs, file_count = self._compute_timestamp(path, scan_depth, verbose)
        
        # Cache with completeness
        completeness = CacheCompleteness.from_depth(scan_depth)
        entry = SmartCacheEntry(
            path=path,
            computed_mtime=mtime,
            completeness=completeness,
            actual_depth=scan_depth,
            has_subdirs=has_subdirs,
            file_count=file_count,
            computation_time=time.time()
        )
        
        self._add_to_cache(entry)
        return mtime, completeness
    
    def _determine_smart_depth(self, path: Path, verbose: int) -> int:
        """
        Determine optimal scan depth for smart strategy.
        """
        # Quick check for folder structure
        try:
            entries = list(os.scandir(path))
            subdirs = [e for e in entries if e.is_dir() and not is_system_generated(e.name)]
            
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
    
    def _compute_timestamp(self, path: Path, scan_depth: int, verbose: int) -> Tuple[int, bool, int]:
        """
        Compute timestamp for folder up to specified depth.
        Returns (max_mtime, has_subdirs, file_count).
        """
        max_time = 0
        has_subdirs = False
        file_count = 0
        
        def scan_recursive(current_path: Path, current_depth: int) -> int:
            nonlocal has_subdirs, file_count
            local_max = 0
            
            if current_depth >= scan_depth:
                return 0
                
            try:
                for entry in os.scandir(current_path):
                    if is_system_generated(entry.name):
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
                        if current_depth + 1 < scan_depth:
                            # Recurse into subdirectory
                            sub_max = scan_recursive(Path(entry.path), current_depth + 1)
                            local_max = max(local_max, sub_max)
            except (OSError, PermissionError) as e:
                if verbose >= 2:
                    print(f"Permission denied scanning {current_path}: {e}")
                    
            return local_max
        
        max_time = scan_recursive(path, 0)
        return max_time, has_subdirs, file_count
    
    def _add_to_cache(self, entry: SmartCacheEntry):
        """Add entry to cache with memory management."""
        entry_size = 200  # Approximate bytes per entry
        
        # Evict old entries if needed
        while self.current_memory + entry_size > self.memory_limit:
            self._evict_oldest()
        
        self.cache[entry.path] = entry
        self.current_memory += entry_size
    
    def _evict_oldest(self):
        """Evict oldest incomplete entries first."""
        if not self.cache:
            return
            
        # Sort by completeness (incomplete first) then by time
        candidates = sorted(
            self.cache.items(),
            key=lambda x: (x[1].completeness.value, x[1].computation_time)
        )
        
        # Evict least complete, oldest entry
        path_to_evict = candidates[0][0]
        del self.cache[path_to_evict]
        self.current_memory -= 200
        self.evictions += 1
    
    def get_statistics(self) -> Dict[str, int]:
        """Get cache statistics for debugging."""
        return {
            'entries': len(self.cache),
            'memory_bytes': self.current_memory,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0