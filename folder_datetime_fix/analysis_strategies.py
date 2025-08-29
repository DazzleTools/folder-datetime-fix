"""
Analysis strategy implementations for folder datetime fix.

This module provides different strategies for analyzing and processing folders,
allowing optimization for different use cases (memory, speed, network shares).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from .folder_scanner import FolderScanner
from .trace_utils import trace


class AnalysisStrategy(ABC):
    """Base class for folder analysis strategies."""
    
    def __init__(self, scanner: FolderScanner):
        """
        Initialize the strategy with a scanner instance.
        
        Args:
            scanner: FolderScanner instance to use for operations
        """
        self.scanner = scanner
    
    @abstractmethod
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """
        Analyze folders and collect timestamps.
        
        Args:
            base_path: Starting directory
            depths: List of depths to process
        
        Returns:
            List of (folder_path, timestamp) tuples
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the strategy name for display."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a description of the strategy."""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Return strategy configuration for debugging."""
        return {
            'name': self.get_name(),
            'description': self.get_description(),
            'cache_enabled': self.scanner.use_cache,
            'skip_generated': self.scanner.skip_generated
        }


class StandardStrategy(AnalysisStrategy):
    """Standard streaming strategy with smart caching (default)."""
    
    def __init__(self, scanner: FolderScanner, scan_strategy: str = 'shallow'):
        """
        Initialize standard strategy.
        
        Args:
            scanner: FolderScanner instance
            scan_strategy: 'shallow', 'deep', or 'smart'
        """
        super().__init__(scanner)
        self.scan_strategy = scan_strategy
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Use standard scan_and_collect with caching."""
        return self.scanner.scan_and_collect(
            base_path, 
            depths, 
            strategy=self.scan_strategy,
            use_max_depth_detection=True
        )
    
    def get_name(self) -> str:
        return f"standard-{self.scan_strategy}"
    
    def get_description(self) -> str:
        return f"Standard streaming with {self.scan_strategy} scanning and smart caching"


class LowMemoryStrategy(AnalysisStrategy):
    """Ultra-low memory strategy - no caching, minimal state."""
    
    def __init__(self, scanner: FolderScanner, scan_strategy: str = 'shallow'):
        """
        Initialize low memory strategy.
        
        Args:
            scanner: FolderScanner instance (cache will be disabled)
            scan_strategy: 'shallow', 'deep', or 'smart'
        """
        super().__init__(scanner)
        # Force disable cache for low memory mode
        self.scanner.use_cache = False
        self.scanner.cache = None
        self.scan_strategy = scan_strategy
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Process folders with minimal memory usage."""
        # Use standard scan but with cache disabled
        return self.scanner.scan_and_collect(
            base_path,
            depths,
            strategy=self.scan_strategy,
            use_max_depth_detection=True
        )
    
    def get_name(self) -> str:
        return f"low-memory-{self.scan_strategy}"
    
    def get_description(self) -> str:
        return f"Ultra-low memory mode with {self.scan_strategy} scanning (no caching)"


class TreeStrategy(AnalysisStrategy):
    """Memory-efficient tree structure with bottom-up timestamp computation."""
    
    class FolderNode:
        """Minimal folder node for tree structure."""
        __slots__ = ['name', 'depth', 'children', 'computed_mtime', 'is_calculated', 'full_path']
        
        def __init__(self, name: str, depth: int, full_path: Path):
            self.name = name
            self.depth = depth
            self.children = []
            self.computed_mtime = None
            self.is_calculated = False
            self.full_path = full_path
    
    def __init__(self, scanner: FolderScanner):
        """
        Initialize tree strategy.
        
        Args:
            scanner: FolderScanner instance
        """
        super().__init__(scanner)
        self.root = None
        # Use moderate caching for tree mode
        self.scanner.use_cache = True
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Build tree structure and compute timestamps bottom-up."""
        from .system_files import is_system_generated
        
        base_path = Path(base_path).resolve()
        depth_set = set(depths) if depths else set(range(100))
        
        # Build tree structure
        self.root = self.FolderNode(base_path.name, 0, base_path)
        self._build_tree(self.root, base_path, max(depths) if depths else 100)
        
        # Compute timestamps bottom-up
        self._compute_timestamps_bottom_up(self.root)
        
        # Extract results for requested depths
        results = []
        self._extract_at_depths(self.root, depth_set, results)
        
        if self.scanner.verbose >= 1:
            total_folders = len(results)
            print(f"Tree mode: Processed {total_folders:,} folders with bottom-up computation")
        
        return results
    
    def _build_tree(self, node: FolderNode, path: Path, max_depth: int):
        """Build tree structure recursively."""
        from .system_files import is_system_generated
        
        if node.depth >= max_depth:
            return
        
        try:
            import os
            for entry in os.scandir(path):
                if entry.is_dir() and not is_system_generated(entry.name):
                    child_path = Path(entry.path)
                    child = self.FolderNode(entry.name, node.depth + 1, child_path)
                    node.children.append(child)
                    self._build_tree(child, child_path, max_depth)
        except (PermissionError, OSError):
            pass
    
    def _compute_timestamps_bottom_up(self, node: FolderNode) -> Optional[datetime]:
        """Compute timestamps using bottom-up traversal."""
        if node.is_calculated:
            return node.computed_mtime
        
        # First compute all children (bottom-up)
        max_time = None
        for child in node.children:
            child_time = self._compute_timestamps_bottom_up(child)
            if child_time and (not max_time or child_time > max_time):
                max_time = child_time
        
        # Then compute this folder's timestamp
        folder_time = self.scanner.get_smart_timestamp(node.full_path)
        
        # Use the maximum of folder's own time and children's times
        if folder_time:
            if not max_time or folder_time > max_time:
                max_time = folder_time
        
        node.computed_mtime = max_time
        node.is_calculated = True
        return max_time
    
    def _extract_at_depths(self, node: FolderNode, depth_set: set, results: list):
        """Extract folders at requested depths."""
        if node.depth in depth_set:
            results.append((node.full_path, node.computed_mtime))
        
        for child in node.children:
            self._extract_at_depths(child, depth_set, results)
    
    def get_name(self) -> str:
        return "tree"
    
    def get_description(self) -> str:
        return "Memory-efficient tree with bottom-up timestamp computation"


class FolderOnlyStrategy(AnalysisStrategy):
    """Ultra-minimal mode - computes timestamps without storing files in memory."""
    
    def __init__(self, scanner: FolderScanner):
        """
        Initialize folder-only strategy.
        Processes files on-the-fly without storing them.
        
        Args:
            scanner: FolderScanner instance
        """
        super().__init__(scanner)
        # Enable cache for storing computed timestamps and completeness tracking
        self.scanner.use_cache = True
        # Ensure cache exists
        if self.scanner.use_cache and not self.scanner.cache:
            from .cache import SmartStreamingCache
            self.scanner.cache = SmartStreamingCache(memory_limit_mb=100)
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """
        Process folders efficiently by computing timestamps on-the-fly.
        Files are processed but not stored in memory.
        Uses cache with completeness tracking for efficiency.
        """
        import os
        from datetime import datetime
        from .system_files import is_system_generated
        from .cache import CacheCompleteness, SmartCacheEntry
        
        results = []
        base_path = Path(base_path).resolve()
        
        # Convert depths list to a set for O(1) lookup
        depth_set = set(depths) if depths else set(range(100))
        max_requested_depth = max(depths) if depths else 99
        
        # Track folders at each depth for statistics
        folders_by_depth = {}
        folders_with_timestamps = 0
        cache_hits = 0
        cache_misses = 0
        
        # Walk the tree and compute timestamps on-the-fly
        for root, dirs, files in os.walk(base_path):
            root_path = Path(root)
            
            # Calculate current depth
            try:
                relative = root_path.relative_to(base_path)
                current_depth = len(relative.parts)
            except ValueError:
                current_depth = 0
            
            # Skip if depth not requested
            if current_depth not in depth_set:
                # Still need to filter dirs for next iteration
                if self.scanner.skip_generated and dirs:
                    dirs[:] = [d for d in dirs if not is_system_generated(d)]
                continue
            
            # Check cache first if enabled
            cached_used = False
            if self.scanner.cache and root_path in self.scanner.cache.cache:
                cached_entry = self.scanner.cache.cache[root_path]
                
                # Check if cache is sufficient for our needs
                if self._is_cache_sufficient(cached_entry, current_depth, max_requested_depth):
                    # Use cached result
                    timestamp = datetime.fromtimestamp(cached_entry.computed_mtime) if cached_entry.computed_mtime > 0 else None
                    results.append((root_path, timestamp))
                    
                    if timestamp is not None:
                        folders_with_timestamps += 1
                    cache_hits += 1
                    cached_used = True
                    
                    # Track statistics
                    if current_depth not in folders_by_depth:
                        folders_by_depth[current_depth] = 0
                    folders_by_depth[current_depth] += 1
                    
                    # Prune traversal if cache says complete
                    if cached_entry.completeness == CacheCompleteness.COMPLETE:
                        dirs.clear()
                    continue
            
            if not cached_used:
                cache_misses += 1
            
            # Filter system directories before processing
            if self.scanner.skip_generated and dirs:
                dirs[:] = [d for d in dirs if not is_system_generated(d)]
            
            # Compute timestamp for this folder by processing files on-the-fly
            # This is the key difference - we compute but don't store files
            max_time = None
            
            try:
                # Process files immediately without storing them
                for file in files:
                    if self.scanner.skip_generated and is_system_generated(file):
                        continue
                    
                    file_path = root_path / file
                    try:
                        mtime = file_path.stat().st_mtime
                        file_datetime = datetime.fromtimestamp(mtime)
                        
                        if max_time is None or file_datetime > max_time:
                            max_time = file_datetime
                    except (OSError, PermissionError):
                        continue
                
                # Also check immediate subdirectory timestamps
                for dir_name in dirs:
                    if self.scanner.skip_generated and is_system_generated(dir_name):
                        continue
                    
                    dir_path = root_path / dir_name
                    try:
                        mtime = dir_path.stat().st_mtime
                        dir_datetime = datetime.fromtimestamp(mtime)
                        
                        if max_time is None or dir_datetime > max_time:
                            max_time = dir_datetime
                    except (OSError, PermissionError):
                        continue
                        
            except (OSError, PermissionError):
                pass
            
            # Determine completeness level for this folder
            has_subdirs = len(dirs) > 0
            if not has_subdirs:
                # No subdirectories means this folder is complete
                completeness = CacheCompleteness.COMPLETE
            elif current_depth >= max_requested_depth:
                # At max depth, we only looked at immediate children
                completeness = CacheCompleteness.SHALLOW
            else:
                # Calculate how deep we're scanning from this point
                remaining_depth = max_requested_depth - current_depth
                if remaining_depth >= 999:
                    completeness = CacheCompleteness.COMPLETE
                else:
                    completeness = CacheCompleteness.from_depth(remaining_depth)
            
            # Store in cache if enabled
            if self.scanner.cache:
                import time
                cache_entry = SmartCacheEntry(
                    path=root_path,
                    computed_mtime=max_time.timestamp() if max_time else 0,
                    completeness=completeness,
                    has_subdirs=has_subdirs,
                    file_count=len(files),
                    actual_depth=remaining_depth if current_depth < max_requested_depth else 0,
                    computation_time=time.time()  # Track when this was computed
                )
                self.scanner.cache.cache[root_path] = cache_entry
                
                if self.scanner.verbose >= 3:
                    print(f"  Cached {root_path.name}: completeness={completeness.name}")
            
            # Add result with computed timestamp
            results.append((root_path, max_time))
            
            if max_time is not None:
                folders_with_timestamps += 1
            
            # Track folder count by depth for statistics
            if current_depth not in folders_by_depth:
                folders_by_depth[current_depth] = 0
            folders_by_depth[current_depth] += 1
            
            # Stop traversing deeper if we've exceeded all requested depths
            if depths and current_depth >= max_requested_depth:
                dirs.clear()
        
        # Report statistics if verbose
        if self.scanner.verbose >= 1:
            total_folders = len(results)
            print(f"FolderOnly mode: Processed {total_folders:,} folders")
            print(f"  Computed timestamps: {folders_with_timestamps:,}")
            print(f"  Without timestamps: {total_folders - folders_with_timestamps:,}")
            if self.scanner.cache and (cache_hits + cache_misses) > 0:
                print(f"  Cache hits: {cache_hits:,}")
                print(f"  Cache misses: {cache_misses:,}")
                hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100
                print(f"  Cache hit rate: {hit_rate:.1f}%")
            if self.scanner.verbose >= 2 and folders_by_depth:
                print("Folders by depth:")
                for depth in sorted(folders_by_depth.keys()):
                    print(f"  Depth {depth}: {folders_by_depth[depth]:,} folders")
        
        return results
    
    def _is_cache_sufficient(self, cached_entry, current_depth: int, 
                            max_requested_depth: int) -> bool:
        """
        Check if cached completeness is sufficient for current request.
        """
        from .cache import CacheCompleteness
        
        # Complete is always sufficient
        if cached_entry.completeness == CacheCompleteness.COMPLETE:
            return True
        
        # Beyond requested depth is always sufficient  
        if current_depth > max_requested_depth:
            return True
        
        # Check if cached depth coverage is sufficient
        needed_depth = max_requested_depth - current_depth
        
        if cached_entry.completeness == CacheCompleteness.SHALLOW:
            return needed_depth <= 1
        elif cached_entry.completeness == CacheCompleteness.PARTIAL_2:
            return needed_depth <= 2
        elif cached_entry.completeness == CacheCompleteness.PARTIAL_3:
            return needed_depth <= 3
        elif cached_entry.completeness == CacheCompleteness.PARTIAL_N:
            # Check actual depth if stored
            return cached_entry.actual_depth >= needed_depth if hasattr(cached_entry, 'actual_depth') else False
        
        # Conservative: recompute if unsure
        return False
    
    def get_name(self) -> str:
        return "folder-only"
    
    def get_description(self) -> str:
        return "Ultra-minimal mode - computes timestamps without storing files, with cache completeness tracking"


class AutoStrategy(AnalysisStrategy):
    """Automatically select best strategy based on path characteristics."""
    
    # Cache entry size estimate (bytes)
    BYTES_PER_ENTRY = 350
    
    @classmethod
    def get_system_threshold(cls) -> int:
        """
        Calculate threshold based on system memory.
        
        Returns:
            Maximum folders to cache before switching to low-memory mode
        """
        try:
            import psutil
            total_memory = psutil.virtual_memory().total
        except:
            # Fallback if psutil not available - assume 16GB
            total_memory = 16 * 1024 * 1024 * 1024
        
        # Target 1% of RAM for cache (reasonable for most systems)
        target_memory = total_memory * 0.01
        
        # Calculate folder count
        threshold = int(target_memory / cls.BYTES_PER_ENTRY)
        
        # Apply reasonable bounds
        # Minimum: 50K folders (17MB) for very low memory systems
        threshold = max(threshold, 50_000)
        
        # Maximum: 2M folders (700MB) - no need for gigabytes of cache
        threshold = min(threshold, 2_000_000)
        
        return threshold
    
    def __init__(self, scanner: FolderScanner, threshold_multiplier: float = 1.0):
        """
        Initialize auto strategy with system-specific threshold.
        
        Args:
            scanner: FolderScanner instance
            threshold_multiplier: Multiply threshold by this value (e.g., 0.5 for lower, 2.0 for higher)
        """
        super().__init__(scanner)
        self.selected_strategy = None
        
        # Calculate system-specific threshold
        base_threshold = self.get_system_threshold()
        self.threshold = int(base_threshold * threshold_multiplier)
        
        if scanner.verbose >= 2:
            try:
                import psutil
                total_gb = psutil.virtual_memory().total / (1024**3)
                cache_mb = (self.threshold * self.BYTES_PER_ENTRY) / (1024**2)
                print(f"AutoStrategy: System RAM={total_gb:.1f}GB, Threshold={self.threshold:,} folders (~{cache_mb:.0f}MB cache)")
            except:
                cache_mb = (self.threshold * self.BYTES_PER_ENTRY) / (1024**2)
                print(f"AutoStrategy: Threshold={self.threshold:,} folders (~{cache_mb:.0f}MB cache)")
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Automatically select and use best strategy."""
        # Detect characteristics
        is_network = str(base_path).startswith('\\\\') or str(base_path).startswith('//')
        
        # Quick sample to estimate size
        folder_count = 0
        max_depth_sample = min(3, max(depths) if depths else 3)
        
        try:
            import os
            for root, dirs, _ in os.walk(base_path):
                folder_count += 1
                # Sample only first few levels
                depth = len(Path(root).relative_to(base_path).parts)
                if depth >= max_depth_sample:
                    dirs.clear()  # Stop traversing deeper
                if folder_count > 1000:
                    break  # Enough sampling
        except:
            pass
        
        # Select strategy based on folder count vs threshold
        # Network consideration: use 'shallow' scanning for network paths to reduce latency
        # Local paths can use 'smart' scanning for better accuracy
        
        if folder_count > self.threshold:
            # Large tree - use low memory mode
            scan_mode = 'shallow' if is_network else 'smart'
            self.selected_strategy = LowMemoryStrategy(self.scanner, scan_mode)
            if self.scanner.verbose >= 1:
                path_type = "network share" if is_network else "local tree"
                print(f"Auto-selected: Low-memory strategy for large {path_type} ({folder_count:,}+ folders exceed {self.threshold:,} threshold)")
        else:
            # Normal size - use standard with caching
            scan_mode = 'shallow' if is_network else 'smart'
            self.selected_strategy = StandardStrategy(self.scanner, scan_mode)
            if self.scanner.verbose >= 1:
                path_type = "network share" if is_network else "local path"
                cache_mb = (folder_count * self.BYTES_PER_ENTRY) / (1024**2)
                print(f"Auto-selected: Standard strategy with caching for {path_type} ({folder_count:,} folders, ~{cache_mb:.0f}MB cache)")
        
        # Use selected strategy
        return self.selected_strategy.analyze(base_path, depths)
    
    def get_name(self) -> str:
        if self.selected_strategy:
            return f"auto({self.selected_strategy.get_name()})"
        return "auto"
    
    def get_description(self) -> str:
        return "Automatically select best strategy based on path characteristics"


class StrategyFactory:
    """Factory for creating analysis strategies."""
    
    @staticmethod
    def create_strategy(analyze_param: str, scanner: FolderScanner, scan_strategy: str = 'shallow') -> AnalysisStrategy:
        """
        Create an analysis strategy from parameter string.
        
        Args:
            analyze_param: Strategy parameter from --analyze flag
                Examples: 'auto', 'auto=2.0', 'standard,no-cache', 'low-memory'
            scanner: FolderScanner instance
            scan_strategy: Scan strategy ('shallow', 'deep', 'smart')
        
        Returns:
            AnalysisStrategy instance
        """
        analyze_param = analyze_param.lower().strip()
        
        # Parse comma-separated options
        options = [opt.strip() for opt in analyze_param.split(',')]
        primary = options[0] if options else 'auto'
        
        # Parse threshold multiplier for auto strategy (e.g., "auto=2.0")
        threshold_multiplier = 1.0
        if '=' in primary and primary.startswith('auto'):
            parts = primary.split('=')
            primary = parts[0]
            try:
                threshold_multiplier = float(parts[1])
            except (ValueError, IndexError):
                threshold_multiplier = 1.0
        
        # Handle special modifiers
        force_no_cache = 'no-cache' in options
        force_low_memory = 'low-memory' in options
        
        # Create base strategy
        if primary == 'tree':
            strategy = TreeStrategy(scanner)
        elif primary == 'folder-only' or primary == 'folders':
            strategy = FolderOnlyStrategy(scanner)
        elif primary == 'low-memory' or force_low_memory:
            strategy = LowMemoryStrategy(scanner, scan_strategy)
        elif primary == 'auto':
            strategy = AutoStrategy(scanner, threshold_multiplier)
        else:
            # Default to standard
            strategy = StandardStrategy(scanner, scan_strategy)
        
        # Apply modifiers
        if force_no_cache and hasattr(strategy, 'scanner'):
            strategy.scanner.use_cache = False
            strategy.scanner.cache = None
        
        return strategy
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """Return list of available strategy names."""
        return ['auto', 'standard', 'low-memory', 'tree', 'folder-only']