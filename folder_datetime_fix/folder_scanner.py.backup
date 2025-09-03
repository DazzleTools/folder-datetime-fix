"""
Folder scanner module for depth-based directory traversal and timestamp collection.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union
from .trace_utils import trace
from .cache import SmartStreamingCache, CacheCompleteness
from .exclusion_filter import ExclusionFilter


class FolderScanner:
    """Scans folders and collects timestamp information based on depth and strategy."""
    
    def __init__(self, skip_generated: bool = False, verbose: int = 0, use_cache: bool = True,
                 exclusion_filter: Optional[ExclusionFilter] = None):
        """
        Initialize the scanner.
        
        Args:
            skip_generated: (Legacy) If True, exclude system-generated files from timestamp calculation
            verbose: Verbosity level (0=quiet, 1=basic, 2=detailed, 3=debug, 4=trace)
            use_cache: If True, enable smart caching for performance
            exclusion_filter: Advanced exclusion filter with glob patterns (overrides skip_generated)
        """
        self.verbose = verbose
        self.use_cache = use_cache
        self.cache = SmartStreamingCache(memory_limit_mb=100) if use_cache else None
        
        # Use exclusion filter if provided, otherwise create from legacy flag
        if exclusion_filter is not None:
            self.exclusion_filter = exclusion_filter
            self.skip_generated = False  # Not used when filter is provided
        else:
            # Legacy compatibility
            self.skip_generated = skip_generated
            self.exclusion_filter = ExclusionFilter.from_legacy(skip_generated)
    
    def detect_max_depth(self, base_path: Path, limit: int = 100) -> int:
        """
        Quickly detect the actual maximum depth of a directory tree.
        
        Args:
            base_path: Starting directory
            limit: Safety limit to prevent infinite recursion (default 100)
        
        Returns:
            Maximum depth found in the tree
        """
        base_path = Path(base_path).resolve()
        max_depth = 0
        
        if self.verbose >= 2:
            print(f"Detecting maximum depth of tree at {base_path}...")
        
        try:
            for root, dirs, _ in os.walk(base_path):
                # Filter out excluded directories from further traversal FIRST
                # This must happen before we process the current directory
                if dirs:
                    # This modifies dirs in-place to control os.walk traversal
                    filtered_dirs = []
                    for d in dirs:
                        dir_path = Path(root) / d
                        if not self.exclusion_filter.should_exclude(dir_path, is_dir=True):
                            filtered_dirs.append(d)
                    dirs[:] = filtered_dirs
                
                # Skip excluded directories if needed
                if root != str(base_path):
                    # Check if current directory should be excluded
                    current_path = Path(root)
                    if self.exclusion_filter.should_exclude(current_path, is_dir=True):
                        # This directory shouldn't have been visited if parent filtered correctly
                        # but handle it anyway for robustness
                        continue
                
                # Calculate depth relative to base
                try:
                    rel_path = Path(root).relative_to(base_path)
                    if rel_path == Path('.'):
                        current_depth = 0
                    else:
                        current_depth = len(rel_path.parts)
                except ValueError:
                    # Should not happen, but handle gracefully
                    continue
                
                # Update max depth
                if current_depth > max_depth:
                    max_depth = current_depth
                    if self.verbose >= 3:
                        print(f"  New max depth: {max_depth} at {rel_path}")
                
                # Safety limit
                if max_depth >= limit:
                    if self.verbose >= 1:
                        print(f"  Reached depth limit of {limit}, stopping detection")
                    break
                    
        except PermissionError as e:
            if self.verbose >= 2:
                print(f"  Permission denied during depth detection: {e}")
        
        if self.verbose >= 1:
            print(f"Maximum tree depth detected: {max_depth}")
            
        return max_depth
    
    @trace
    def get_folders_at_depth(self, base_path: Path, depth: int) -> List[Path]:
        """
        Get all folders at a specific depth from the base path.
        
        Args:
            base_path: Starting directory
            depth: How many levels down to look (0 = base itself)
        
        Returns:
            List of folder paths at the specified depth
        """
        base_path = Path(base_path).resolve()
        
        if depth == 0:
            return [base_path] if base_path.is_dir() else []
        
        folders = []
        
        def _traverse(current_path: Path, current_depth: int):
            if current_depth == depth:
                if current_path.is_dir():
                    folders.append(current_path)
                return
            
            if current_depth < depth and current_path.is_dir():
                try:
                    for child in current_path.iterdir():
                        if child.is_dir():
                            _traverse(child, current_depth + 1)
                except PermissionError:
                    pass  # Skip folders we can't access
        
        _traverse(base_path, 0)
        return sorted(folders)
    
    @trace
    def get_shallow_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Get the most recent timestamp from immediate children only.
        
        Args:
            folder_path: Directory to scan
        
        Returns:
            Most recent timestamp or None if no valid files
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        # Use cache if available
        if self.use_cache and self.cache:
            mtime, completeness = self.cache.get_or_compute(
                folder_path, "shallow", verbose=self.verbose
            )
            if mtime > 0:
                return datetime.fromtimestamp(mtime)
            return None
        
        latest_time = None
        
        try:
            for item in folder_path.iterdir():
                # Skip if it's a directory
                if item.is_dir():
                    continue
                
                # Skip excluded files
                if self.exclusion_filter.should_exclude(item, is_dir=False):
                    continue
                
                try:
                    # Get modified time
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if latest_time is None or mtime > latest_time:
                        latest_time = mtime
                
                except (OSError, PermissionError):
                    continue  # Skip files we can't access
        
        except PermissionError:
            return None
        
        return latest_time
    
    @trace
    def get_deep_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Get the most recent timestamp from entire subtree.
        
        Args:
            folder_path: Directory to scan recursively
        
        Returns:
            Most recent timestamp or None if no valid files
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        # Use cache if available
        if self.use_cache and self.cache:
            mtime, completeness = self.cache.get_or_compute(
                folder_path, "deep", verbose=self.verbose
            )
            if mtime > 0:
                return datetime.fromtimestamp(mtime)
            return None
        
        latest_time = None
        visited = set()  # Track visited paths to avoid circular references
        
        def _scan_recursive(current_path: Path):
            nonlocal latest_time
            
            # Avoid circular references (junctions/symlinks)
            real_path = current_path.resolve()
            if real_path in visited:
                return
            visited.add(real_path)
            
            try:
                for item in current_path.iterdir():
                    if item.is_dir():
                        # Recurse into subdirectories
                        _scan_recursive(item)
                    else:
                        # Skip excluded files
                        if self.exclusion_filter.should_exclude(item, is_dir=False):
                            continue
                        
                        try:
                            # Get modified time
                            mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            
                            if latest_time is None or mtime > latest_time:
                                latest_time = mtime
                        
                        except (OSError, PermissionError):
                            continue
            
            except PermissionError:
                pass  # Skip folders we can't access
        
        _scan_recursive(folder_path)
        return latest_time
    
    @trace
    def get_smart_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Use heuristics to decide between shallow and deep scanning.
        
        Args:
            folder_path: Directory to scan
        
        Returns:
            Most recent timestamp using smart strategy
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        # Use cache if available
        if self.use_cache and self.cache:
            mtime, completeness = self.cache.get_or_compute(
                folder_path, "smart", verbose=self.verbose
            )
            if mtime > 0:
                return datetime.fromtimestamp(mtime)
            return None
        
        # Check if folder has subdirectories
        has_subdirs = False
        try:
            for item in folder_path.iterdir():
                if item.is_dir():
                    has_subdirs = True
                    break
        except PermissionError:
            return None
        
        # If it has subdirectories, go deep; otherwise shallow
        if has_subdirs:
            return self.get_deep_timestamp(folder_path)
        else:
            return self.get_shallow_timestamp(folder_path)
    
    @trace
    def scan_and_collect(self, base_path: Path, depths: List[int], 
                        strategy: str = 'shallow', use_max_depth_detection: bool = True) -> List[Tuple[Path, Optional[datetime]]]:
        """
        Scan folders at specified depths and collect their timestamps.
        
        Args:
            base_path: Starting directory
            depths: List of depths to process
            strategy: 'shallow', 'deep', or 'smart'
            use_max_depth_detection: If True, detect actual max depth first
        
        Returns:
            List of (folder_path, timestamp) tuples
        """
        results = []
        processed = set()  # Avoid processing same folder twice
        
        # For infinite depth operations, detect actual max depth first
        if use_max_depth_detection and depths and max(depths) > 20:
            actual_max = self.detect_max_depth(base_path, limit=max(depths))
            if actual_max < max(depths):
                # Filter depths to only those that exist
                original_count = len(depths)
                depths = [d for d in depths if d <= actual_max]
                if self.verbose >= 1 and len(depths) < original_count:
                    print(f"Optimized: Reduced depths from {original_count} to {len(depths)} based on actual tree depth of {actual_max}")
        
        if self.verbose >= 3:
            print(f"Scanning with strategy: {strategy}")
            print(f"Processing depths: {depths}")
        
        # Track consecutive empty depths for early termination
        consecutive_empty = 0
        max_depth_reached = -1
        
        for depth in sorted(depths):
            if self.verbose >= 2:
                print(f"Scanning at depth {depth}...")
            
            folders = self.get_folders_at_depth(base_path, depth)
            
            if self.verbose >= 2:
                print(f"Found {len(folders)} folders at depth {depth}")
            
            # Early termination optimization
            if len(folders) == 0:
                consecutive_empty += 1
                # Allow one gap in case of unusual tree structure, but stop after 2 consecutive empty
                if consecutive_empty >= 2 and depth > 0:
                    if self.verbose >= 1:
                        print(f"Stopping scan early - no folders found after depth {max_depth_reached}")
                    break
            else:
                consecutive_empty = 0
                max_depth_reached = depth
            
            for idx, folder in enumerate(folders, 1):
                if folder in processed:
                    continue
                processed.add(folder)
                
                if self.verbose >= 3:
                    print(f"Processing: {folder}")
                elif self.verbose >= 2 and len(folders) > 10:
                    # Show progress for large folder sets
                    if idx % 10 == 0 or idx == len(folders):
                        print(f"  Progress: {idx}/{len(folders)} folders processed...")
                
                # Get timestamp based on strategy
                if strategy == 'shallow':
                    timestamp = self.get_shallow_timestamp(folder)
                    results.append((folder, timestamp))
                elif strategy == 'deep':
                    # For deep strategy, we need to fix ALL subfolders too
                    timestamp = self.get_deep_timestamp(folder)
                    results.append((folder, timestamp))
                    
                    # When using deep strategy, also process all subfolders
                    # This ensures intermediate folders get fixed
                    for root, dirs, _ in os.walk(folder):
                        root_path = Path(root)
                        if root_path != folder and root_path not in processed:
                            # Each subfolder gets the timestamp of its own subtree
                            subfolder_timestamp = self.get_deep_timestamp(root_path)
                            results.append((root_path, subfolder_timestamp))
                            processed.add(root_path)
                            
                elif strategy == 'smart':
                    timestamp = self.get_smart_timestamp(folder)
                    results.append((folder, timestamp))
                    
                    # For smart strategy with subdirs, also process them
                    if any(p.is_dir() for p in folder.iterdir()):
                        for root, dirs, _ in os.walk(folder):
                            root_path = Path(root)
                            if root_path != folder and root_path not in processed:
                                subfolder_timestamp = self.get_smart_timestamp(root_path)
                                results.append((root_path, subfolder_timestamp))
                                processed.add(root_path)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")
        
        # Report cache statistics if verbose
        if self.use_cache and self.cache and self.verbose >= 2:
            stats = self.cache.get_statistics()
            print(f"\nCache Statistics:")
            print(f"  Hits: {stats['hits']}")
            print(f"  Misses: {stats['misses']}")
            print(f"  Hit Rate: {stats['hit_rate']:.1%}")
            print(f"  Entries: {stats['entries']}")
            print(f"  Memory: {stats['memory_bytes']:,} bytes")
        
        return results