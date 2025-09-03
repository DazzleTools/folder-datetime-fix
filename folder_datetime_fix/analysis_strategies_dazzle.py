"""
Analysis strategy implementations using DazzleTreeLib.

This module provides different strategies for analyzing and processing folders,
using DazzleTreeLib's composable adapter pattern for optimization.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import asyncio

from dazzletreelib.aio import (
    AsyncFileSystemNode,
    AsyncFileSystemAdapter,
    TimestampCalculationAdapter,
    CompletenessAwareCacheAdapter,
    DepthTrackingAdapter,
    traverse_tree_bottom_up,
    traverse_tree_by_level,
    process_folders_bottom_up,
)
from .trace_utils import trace
from .exclusion_filter import ExclusionFilter


class DazzleStrategy(ABC):
    """Base class for DazzleTreeLib-based analysis strategies."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None, 
                 verbose: int = 0):
        """
        Initialize the strategy with DazzleTreeLib adapters.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
        """
        self.exclusion_filter = exclusion_filter or ExclusionFilter.from_legacy(False)
        self.verbose = verbose
        self.adapter_stack = self._build_adapter_stack()
    
    @abstractmethod
    def _build_adapter_stack(self):
        """Build the adapter stack for this strategy."""
        pass
    
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
        config = {
            'name': self.get_name(),
            'description': self.get_description(),
            'adapter_stack': []
        }
        
        # Trace adapter stack
        adapter = self.adapter_stack
        while adapter:
            config['adapter_stack'].append(adapter.__class__.__name__)
            if hasattr(adapter, 'base_adapter'):
                adapter = adapter.base_adapter
            else:
                break
        
        return config


class StandardDazzleStrategy(DazzleStrategy):
    """Standard streaming strategy with smart caching using DazzleTreeLib."""
    
    def __init__(self, scan_strategy: str = 'shallow', 
                 exclusion_filter: Optional[ExclusionFilter] = None,
                 verbose: int = 0):
        """
        Initialize standard strategy.
        
        Args:
            scan_strategy: 'shallow', 'deep', or 'smart'
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
        """
        self.scan_strategy = scan_strategy
        super().__init__(exclusion_filter, verbose)
    
    def _build_adapter_stack(self):
        """Build adapter stack with caching and timestamp calculation."""
        # Base filesystem adapter
        base = AsyncFileSystemAdapter(
            max_concurrent=50,
            batch_size=256,
            follow_symlinks=False
        )
        
        # Add depth tracking
        depth = DepthTrackingAdapter(base)
        
        # Add timestamp calculation
        timestamp = TimestampCalculationAdapter(depth, strategy=self.scan_strategy)
        
        # Add cache completeness tracking
        cache = CompletenessAwareCacheAdapter(timestamp, max_memory_mb=100)
        
        return cache
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Use DazzleTreeLib traversal with caching."""
        async def _analyze():
            results = []
            processed = set()
            depths_to_process = depths.copy() if depths else []
            
            # Optimize depths if needed
            if depths_to_process and max(depths_to_process) > 20:
                # Detect actual max depth
                actual_max = await self._detect_max_depth(base_path, limit=max(depths_to_process))
                if actual_max < max(depths_to_process):
                    depths_filtered = [d for d in depths_to_process if d <= actual_max]
                    if self.verbose >= 1:
                        print(f"Optimized: Reduced depths from {len(depths_to_process)} to {len(depths_filtered)} based on actual tree depth of {actual_max}")
                    depths_to_process = depths_filtered
            
            # Process each depth
            for target_depth in sorted(depths_to_process):
                if self.verbose >= 2:
                    print(f"Scanning at depth {target_depth}...")
                
                async for level_depth, nodes in traverse_tree_by_level(base_path, max_depth=target_depth):
                    if level_depth == target_depth:
                        for node in nodes:
                            if node.path.is_dir() and str(node.path) not in processed:
                                if not self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    # Get timestamp using adapter
                                    timestamp_adapter = self._get_timestamp_adapter()
                                    timestamp = await timestamp_adapter.calculate_timestamp(node)
                                    results.append((node.path, timestamp))
                                    processed.add(str(node.path))
                        break
            
            return results
        
        return asyncio.run(_analyze())
    
    async def _detect_max_depth(self, base_path: Path, limit: int) -> int:
        """Detect maximum depth of tree."""
        max_depth = 0
        async for depth, _ in traverse_tree_by_level(base_path, max_depth=limit):
            if depth > max_depth:
                max_depth = depth
        return max_depth
    
    def _get_timestamp_adapter(self):
        """Get the timestamp adapter from the stack."""
        adapter = self.adapter_stack
        while adapter:
            if isinstance(adapter, TimestampCalculationAdapter):
                return adapter
            if hasattr(adapter, 'base_adapter'):
                adapter = adapter.base_adapter
            else:
                break
        # Fallback - create new one
        return TimestampCalculationAdapter(
            AsyncFileSystemAdapter(), 
            strategy=self.scan_strategy
        )
    
    def get_name(self) -> str:
        return f"dazzle-standard-{self.scan_strategy}"
    
    def get_description(self) -> str:
        return f"DazzleTreeLib standard streaming with {self.scan_strategy} scanning and smart caching"


class LowMemoryDazzleStrategy(DazzleStrategy):
    """Ultra-low memory strategy using DazzleTreeLib - no caching, minimal state."""
    
    def __init__(self, scan_strategy: str = 'shallow',
                 exclusion_filter: Optional[ExclusionFilter] = None,
                 verbose: int = 0):
        """
        Initialize low memory strategy.
        
        Args:
            scan_strategy: 'shallow', 'deep', or 'smart'
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
        """
        self.scan_strategy = scan_strategy
        super().__init__(exclusion_filter, verbose)
    
    def _build_adapter_stack(self):
        """Build minimal adapter stack without caching."""
        # Base filesystem adapter with reduced concurrency
        base = AsyncFileSystemAdapter(
            max_concurrent=10,  # Reduced for low memory
            batch_size=64,      # Smaller batches
            follow_symlinks=False
        )
        
        # Add timestamp calculation only (no caching) with exclusion filter
        timestamp = TimestampCalculationAdapter(
            base, 
            strategy=self.scan_strategy,
            exclusion_filter=self.exclusion_filter
        )
        
        return timestamp
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Process folders with minimal memory usage."""
        async def _analyze():
            results = []
            
            # Process each depth individually to minimize memory
            for target_depth in sorted(depths):
                if self.verbose >= 2:
                    print(f"Low-memory: Processing depth {target_depth}...")
                
                async for level_depth, nodes in traverse_tree_by_level(base_path, max_depth=target_depth):
                    if level_depth == target_depth:
                        for node in nodes:
                            if node.path.is_dir():
                                if not self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    # Calculate timestamp immediately and release node
                                    timestamp = await self.adapter_stack.calculate_timestamp(node)
                                    results.append((node.path, timestamp))
                        break
                
                # Force garbage collection between depths
                import gc
                gc.collect()
            
            return results
        
        return asyncio.run(_analyze())
    
    def get_name(self) -> str:
        return f"dazzle-low-memory-{self.scan_strategy}"
    
    def get_description(self) -> str:
        return f"DazzleTreeLib ultra-low memory with {self.scan_strategy} scanning (no caching)"


class TreeDazzleStrategy(DazzleStrategy):
    """Tree structure strategy using DazzleTreeLib's bottom-up traversal."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None,
                 verbose: int = 0):
        """
        Initialize tree strategy with bottom-up processing.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
        """
        super().__init__(exclusion_filter, verbose)
    
    def _build_adapter_stack(self):
        """Build adapter stack optimized for tree traversal."""
        # Base filesystem adapter
        base = AsyncFileSystemAdapter(
            max_concurrent=100,  # High concurrency for tree building
            batch_size=256,
            follow_symlinks=False
        )
        
        # Add depth tracking for efficient tree operations
        depth = DepthTrackingAdapter(base)
        
        # Add smart timestamp calculation for folders with exclusion filter
        timestamp = TimestampCalculationAdapter(
            depth, 
            strategy='smart',
            exclusion_filter=self.exclusion_filter
        )
        
        # Add caching with completeness tracking for tree mode
        cache = CompletenessAwareCacheAdapter(timestamp, max_memory_mb=50)
        
        return cache
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Build tree and compute timestamps bottom-up."""
        async def _analyze():
            results = []
            processed = set()
            
            # For tree mode, we collect all folders first, then process bottom-up
            all_folders = {}
            
            # First pass: collect all folders at requested depths
            for target_depth in sorted(depths):
                async for level_depth, nodes in traverse_tree_by_level(base_path, max_depth=target_depth):
                    if level_depth == target_depth:
                        for node in nodes:
                            if node.path.is_dir():
                                if not self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    all_folders[str(node.path)] = (node.path, level_depth)
                        break
            
            # Second pass: compute timestamps bottom-up
            # Sort by depth (deepest first) for bottom-up processing
            sorted_folders = sorted(all_folders.values(), key=lambda x: x[1], reverse=True)
            
            timestamp_adapter = self._get_timestamp_adapter()
            for folder_path, depth in sorted_folders:
                if str(folder_path) not in processed:
                    node = AsyncFileSystemNode(folder_path)
                    # Use smart strategy for tree mode
                    timestamp_adapter.strategy = 'smart'
                    timestamp = await timestamp_adapter.calculate_timestamp(node)
                    results.append((folder_path, timestamp))
                    processed.add(str(folder_path))
            
            if self.verbose >= 1:
                print(f"Tree mode: Processed {len(results)} folders with bottom-up computation")
            
            return results
        
        return asyncio.run(_analyze())
    
    def _get_timestamp_adapter(self):
        """Get the timestamp adapter from the stack."""
        adapter = self.adapter_stack
        while adapter:
            if isinstance(adapter, TimestampCalculationAdapter):
                return adapter
            if hasattr(adapter, 'base_adapter'):
                adapter = adapter.base_adapter
            else:
                break
        # Fallback - should not happen in tree strategy
        raise RuntimeError("No TimestampCalculationAdapter found in stack")
    
    def get_name(self) -> str:
        return "dazzle-tree"
    
    def get_description(self) -> str:
        return "DazzleTreeLib tree structure with bottom-up timestamp computation"


class FolderOnlyDazzleStrategy(DazzleStrategy):
    """Ultra-minimal mode using DazzleTreeLib - processes files on-the-fly."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None,
                 verbose: int = 0):
        """
        Initialize folder-only strategy.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
        """
        super().__init__(exclusion_filter, verbose)
    
    def _build_adapter_stack(self):
        """Build adapter stack for folder-only processing."""
        # Base filesystem adapter with conservative settings
        base = AsyncFileSystemAdapter(
            max_concurrent=25,  # Moderate concurrency
            batch_size=128,     # Medium batches
            follow_symlinks=False
        )
        
        # Add shallow timestamp calculation (folder-only) with exclusion filter
        timestamp = TimestampCalculationAdapter(
            base, 
            strategy='shallow',
            exclusion_filter=self.exclusion_filter
        )
        
        # Add lightweight caching
        cache = CompletenessAwareCacheAdapter(timestamp, max_memory_mb=25)
        
        return cache
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Process folders efficiently without storing file details."""
        async def _analyze():
            from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser
            from dazzletreelib.aio import AsyncFileSystemNode
            
            results = []
            
            # Set depth context on cache adapter if available
            if hasattr(self.adapter_stack, 'set_depth_context'):
                # Set context for the deepest level we'll scan
                max_depth = max(depths) if depths else 1
                self.adapter_stack.set_depth_context(max_depth)
            
            # Use our adapter stack with the traverser
            root_node = AsyncFileSystemNode(base_path)
            traverser = AsyncLevelOrderDepthTraverser()
            
            # Process all depths in a single pass
            max_depth = max(depths) if depths else 100
            depth_set = set(depths)
            
            # Use traverse_by_level which accepts an adapter
            async for level_depth, nodes in traverser.traverse_by_level(
                root_node, 
                self.adapter_stack,
                max_depth=max_depth
            ):
                if level_depth in depth_set:
                    for node in nodes:
                        if node.path.is_dir():
                            if not self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                # Get timestamp from our timestamp adapter
                                timestamp_adapter = self._get_timestamp_adapter()
                                if timestamp_adapter:
                                    timestamp = await timestamp_adapter.calculate_timestamp(node)
                                else:
                                    # Fallback - should not happen
                                    timestamp = datetime.fromtimestamp(node.path.stat().st_mtime)
                                
                                results.append((node.path, timestamp))
                
                # Stop if we've processed all requested depths
                if level_depth >= max_depth:
                    break
            
            if self.verbose >= 1:
                print(f"Folder-only mode: Processed {len(results)} folders efficiently")
            
            return results
        
        return asyncio.run(_analyze())
    
    def _get_timestamp_adapter(self):
        """Get the timestamp adapter from the stack."""
        adapter = self.adapter_stack
        while adapter:
            if isinstance(adapter, TimestampCalculationAdapter):
                return adapter
            if hasattr(adapter, 'base_adapter'):
                adapter = adapter.base_adapter
            else:
                break
        return None
    
    def get_name(self) -> str:
        return "dazzle-folder-only"
    
    def get_description(self) -> str:
        return "DazzleTreeLib ultra-minimal with on-the-fly file processing"


# Factory function for creating strategies
def create_strategy(strategy_type: str, scan_strategy: str = 'shallow',
                   exclusion_filter: Optional[ExclusionFilter] = None,
                   verbose: int = 0) -> DazzleStrategy:
    """
    Create a DazzleTreeLib strategy instance.
    
    Args:
        strategy_type: 'standard', 'low-memory', 'tree', or 'folder-only'
        scan_strategy: 'shallow', 'deep', or 'smart' (for applicable strategies)
        exclusion_filter: Filter for excluding files/folders
        verbose: Verbosity level
    
    Returns:
        Strategy instance
    """
    if strategy_type == 'standard':
        return StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose)
    elif strategy_type == 'low-memory':
        return LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose)
    elif strategy_type == 'tree':
        return TreeDazzleStrategy(exclusion_filter, verbose)
    elif strategy_type == 'folder-only':
        return FolderOnlyDazzleStrategy(exclusion_filter, verbose)
    else:
        # Default to standard
        return StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose)


# Backward compatibility aliases
AnalysisStrategy = DazzleStrategy
StandardStrategy = StandardDazzleStrategy
LowMemoryStrategy = LowMemoryDazzleStrategy
TreeStrategy = TreeDazzleStrategy
FolderOnlyStrategy = FolderOnlyDazzleStrategy
# AutoStrategy uses StandardDazzleStrategy with smart scanning
AutoStrategy = StandardDazzleStrategy


class StrategyFactory:
    """Factory for creating analysis strategies - DazzleTreeLib version."""
    
    @staticmethod
    def create_strategy(analyze_param: str, scanner, scan_strategy: str = 'shallow') -> DazzleStrategy:
        """
        Create an analysis strategy from parameter string.
        
        Args:
            analyze_param: Strategy parameter from --analyze flag
                Examples: 'auto', 'auto=2.0', 'standard,no-cache', 'low-memory'
            scanner: FolderScanner instance (for compatibility - gets exclusion filter)
            scan_strategy: Scan strategy ('shallow', 'deep', 'smart')
        
        Returns:
            DazzleStrategy instance
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
        
        # Get exclusion filter and verbosity from scanner
        exclusion_filter = getattr(scanner, 'exclusion_filter', None)
        verbose = getattr(scanner, 'verbose', 0)
        
        # Check for modifiers
        force_low_memory = 'low-memory' in options
        
        # Create base strategy
        if primary == 'tree':
            strategy = TreeDazzleStrategy(exclusion_filter, verbose)
        elif primary == 'folder-only' or primary == 'folders':
            strategy = FolderOnlyDazzleStrategy(exclusion_filter, verbose)
        elif primary == 'low-memory' or force_low_memory:
            strategy = LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose)
        elif primary == 'auto':
            # Check if low-memory modifier is present
            if force_low_memory:
                strategy = LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose)
            else:
                # Auto strategy: use standard for now (could be smarter)
                # TODO: Implement proper auto-selection based on file count
                strategy = StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose)
        else:
            # Default to standard
            strategy = StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose)
        
        return strategy
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """Return list of available strategy names."""
        return ['auto', 'standard', 'low-memory', 'tree', 'folder-only']