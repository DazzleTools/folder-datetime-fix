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
import sys

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

# Try to import the new SmartCachingAdapter
try:
    from dazzletreelib.aio.adapters.smart_caching import SmartCachingAdapter
    SMART_ADAPTER_AVAILABLE = True
except ImportError:
    SMART_ADAPTER_AVAILABLE = False
from .trace_utils import trace
from .exclusion_filter import ExclusionFilter

# Import our local error handling extensions
from dazzletreelib.aio import (
    ErrorHandlingAdapter,
    FailFastPolicy,
    ContinueOnErrorsPolicy,
)


def create_cache_adapter(base_adapter, max_memory_mb=100):
    """
    Create a cache adapter using the best available implementation.

    Prefers SmartCachingAdapter if available for better semantic tracking.
    """
    if SMART_ADAPTER_AVAILABLE:
        # Use the new SmartCachingAdapter with clear semantics
        return SmartCachingAdapter(
            base_adapter=base_adapter,
            max_memory_mb=max_memory_mb,
            track_traversal=True  # Enable discovery/expansion tracking
        )
    else:
        # Fallback to traditional adapter
        return CompletenessAwareCacheAdapter(base_adapter, max_memory_mb=max_memory_mb)


class DazzleStrategy(ABC):
    """Base class for DazzleTreeLib-based analysis strategies."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None, 
                 verbose: int = 0, strict: bool = False):
        """
        Initialize the strategy with DazzleTreeLib adapters.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
            strict: If True, exit on permission errors; if False, continue with warnings
        """
        self.exclusion_filter = exclusion_filter or ExclusionFilter.from_legacy(False)
        self.verbose = verbose
        self.strict = strict
        
        # Create error policy based on strict flag
        if strict:
            self.error_policy = FailFastPolicy()
        else:
            self.error_policy = ContinueOnErrorsPolicy(verbose=verbose >= 1)
        
        # Build adapter stack with error handling
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
            elif hasattr(adapter, '_base_adapter'):
                adapter = adapter._base_adapter
            else:
                break
        
        return config
    
    def get_error_policy(self):
        """Get the error policy if ErrorHandlingAdapter is in the stack."""
        from dazzletreelib.aio import ErrorHandlingAdapter
        
        adapter = self.adapter_stack
        while adapter:
            if isinstance(adapter, ErrorHandlingAdapter):
                return adapter._policy
            # Try different attribute names used by different adapters
            if hasattr(adapter, '_base_adapter'):
                adapter = adapter._base_adapter
            elif hasattr(adapter, 'base_adapter'):
                adapter = adapter.base_adapter
            else:
                break
        return None
    
    def has_error_handling(self) -> bool:
        """Check if error handling is properly configured."""
        return self.get_error_policy() is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return statistics about the analysis, including skipped folders."""
        stats = {}
        
        # Get statistics from error policy if it has them
        if hasattr(self.error_policy, 'skipped_paths'):
            stats['folders_skipped_permission'] = len(self.error_policy.skipped_paths)
            stats['skipped_paths'] = self.error_policy.skipped_paths
        else:
            stats['folders_skipped_permission'] = 0
            stats['skipped_paths'] = []
        
        # Add error details if available
        if hasattr(self.error_policy, 'errors'):
            stats['total_errors'] = len(self.error_policy.errors)
        
        return stats


class StandardDazzleStrategy(DazzleStrategy):
    """Standard streaming strategy with smart caching using DazzleTreeLib."""
    
    def __init__(self, scan_strategy: str = 'shallow', 
                 exclusion_filter: Optional[ExclusionFilter] = None,
                 verbose: int = 0, strict: bool = False):
        """
        Initialize standard strategy.
        
        Args:
            scan_strategy: 'shallow', 'deep', or 'smart'
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
            strict: If True, exit on permission errors; if False, continue with warnings
        """
        self.scan_strategy = scan_strategy
        super().__init__(exclusion_filter, verbose, strict)
    
    def _build_adapter_stack(self):
        """Build adapter stack with caching and timestamp calculation."""
        # Start with base filesystem adapter
        base = AsyncFileSystemAdapter(
            max_concurrent=50,
            batch_size=256,
            follow_symlinks=False
        )
        
        # Wrap with error handling using our policy
        error_handled = ErrorHandlingAdapter(base, self.error_policy)
        
        # Add depth tracking
        depth = DepthTrackingAdapter(error_handled)
        
        # Add timestamp calculation with exclusion filter
        timestamp = TimestampCalculationAdapter(depth, strategy=self.scan_strategy, 
                                               exclusion_filter=self.exclusion_filter)
        
        # Add cache completeness tracking
        cache = create_cache_adapter(timestamp, max_memory_mb=100)

        return cache
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Use DazzleTreeLib traversal with caching."""
        async def _analyze():
            from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser
            from dazzletreelib.aio import AsyncFileSystemNode
            
            results = []
            processed = set()
            depths_to_process = depths.copy() if depths else []
            
            # Create traverser and root node
            traverser = AsyncLevelOrderDepthTraverser()
            root_node = AsyncFileSystemNode(base_path)
            
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
                
                # Use traverser with our adapter stack (which includes error handling)
                async for level_depth, nodes in traverser.traverse_by_level(
                    root_node, self.adapter_stack, max_depth=target_depth
                ):
                    if level_depth == target_depth:
                        for node in nodes:
                            try:
                                # Wrap property access in try-except since it bypasses adapters
                                if not node.path.is_dir():
                                    continue
                                if str(node.path) in processed:
                                    continue
                                if self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    continue
                                    
                                # Get timestamp using adapter
                                timestamp_adapter = self._get_timestamp_adapter()
                                timestamp = await timestamp_adapter.calculate_timestamp(node)
                                results.append((node.path, timestamp))
                                processed.add(str(node.path))
                            except (PermissionError, OSError) as e:
                                # Handle permission errors for inaccessible paths
                                if self.verbose >= 2:
                                    print(f"WARNING: Skipping inaccessible path '{node.path}': {e}")
                                continue
                        break
            
            return results
        
        return asyncio.run(_analyze())
    
    async def _detect_max_depth(self, base_path: Path, limit: int) -> int:
        """Detect maximum depth of tree."""
        from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser
        from dazzletreelib.aio import AsyncFileSystemNode
        
        max_depth = 0
        traverser = AsyncLevelOrderDepthTraverser()
        root_node = AsyncFileSystemNode(base_path)
        
        async for depth, _ in traverser.traverse_by_level(
            root_node, self.adapter_stack, max_depth=limit
        ):
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
                 verbose: int = 0, strict: bool = False):
        """
        Initialize low memory strategy.
        
        Args:
            scan_strategy: 'shallow', 'deep', or 'smart'
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
            strict: If True, exit on permission errors; if False, continue with warnings
        """
        self.scan_strategy = scan_strategy
        super().__init__(exclusion_filter, verbose, strict)
    
    def _build_adapter_stack(self):
        """Build minimal adapter stack without caching."""
        # Base filesystem adapter with reduced concurrency
        base = AsyncFileSystemAdapter(
            max_concurrent=10,  # Reduced for low memory
            batch_size=64,      # Smaller batches
            follow_symlinks=False
        )
        
        # Wrap with error handling using our policy
        error_handled = ErrorHandlingAdapter(base, self.error_policy)
        
        # Add timestamp calculation only (no caching) with exclusion filter
        timestamp = TimestampCalculationAdapter(
            error_handled, 
            strategy=self.scan_strategy,
            exclusion_filter=self.exclusion_filter
        )
        
        return timestamp
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Process folders with minimal memory usage."""
        async def _analyze():
            from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser
            from dazzletreelib.aio import AsyncFileSystemNode
            
            results = []
            traverser = AsyncLevelOrderDepthTraverser()
            root_node = AsyncFileSystemNode(base_path)
            
            # Process each depth individually to minimize memory
            for target_depth in sorted(depths):
                if self.verbose >= 2:
                    print(f"Low-memory: Processing depth {target_depth}...")
                
                async for level_depth, nodes in traverser.traverse_by_level(
                    root_node, self.adapter_stack, max_depth=target_depth
                ):
                    if level_depth == target_depth:
                        for node in nodes:
                            try:
                                # Wrap property access in try-except since it bypasses adapters
                                if not node.path.is_dir():
                                    continue
                                if self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    continue
                                    
                                # Calculate timestamp immediately and release node
                                timestamp = await self.adapter_stack.calculate_timestamp(node)
                                results.append((node.path, timestamp))
                            except (PermissionError, OSError) as e:
                                # Handle permission errors for inaccessible paths
                                if self.verbose >= 2:
                                    print(f"WARNING: Skipping inaccessible path '{node.path}': {e}")
                                continue
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
                 verbose: int = 0, strict: bool = False):
        """
        Initialize tree strategy with bottom-up processing.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
            strict: If True, exit on permission errors; if False, continue with warnings
        """
        super().__init__(exclusion_filter, verbose, strict)
    
    def _build_adapter_stack(self):
        """Build adapter stack optimized for tree traversal."""
        # Base filesystem adapter
        base = AsyncFileSystemAdapter(
            max_concurrent=100,  # High concurrency for tree building
            batch_size=256,
            follow_symlinks=False
        )
        
        # Wrap with error handling using our policy
        error_handled = ErrorHandlingAdapter(base, self.error_policy)
        
        # Add depth tracking for efficient tree operations
        depth = DepthTrackingAdapter(error_handled)
        
        # Add smart timestamp calculation for folders with exclusion filter
        timestamp = TimestampCalculationAdapter(
            depth, 
            strategy='smart',
            exclusion_filter=self.exclusion_filter
        )
        
        # Add caching with completeness tracking for tree mode
        cache = create_cache_adapter(timestamp, max_memory_mb=50)

        return cache
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Build tree and compute timestamps bottom-up."""
        async def _analyze():
            results = []
            processed = set()
            
            # For tree mode, we collect all folders first, then process bottom-up
            all_folders = {}
            
            # Use the adapter stack for traversal - this respects exclusions
            from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser
            traverser = AsyncLevelOrderDepthTraverser()
            root_node = AsyncFileSystemNode(base_path)
            
            # First pass: collect all folders at requested depths
            for target_depth in sorted(depths):
                async for level_depth, nodes in traverser.traverse_by_level(
                    root_node, self.adapter_stack, max_depth=target_depth
                ):
                    if level_depth == target_depth:
                        for node in nodes:
                            try:
                                # Wrap property access in try-except since it bypasses adapters
                                if not node.path.is_dir():
                                    continue
                                if self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                    continue
                                    
                                all_folders[str(node.path)] = (node.path, level_depth)
                            except (PermissionError, OSError) as e:
                                # Handle permission errors for inaccessible paths
                                if self.verbose >= 2:
                                    print(f"WARNING: Skipping inaccessible path '{node.path}': {e}")
                                continue
                        break
            
            # Second pass: compute timestamps bottom-up
            # Sort by depth (deepest first) for bottom-up processing
            sorted_folders = sorted(all_folders.values(), key=lambda x: x[1], reverse=True)
            
            # Use deep strategy for bottom-up to ensure we get all child timestamps
            timestamp_adapter = self._get_timestamp_adapter()
            for folder_path, depth in sorted_folders:
                if str(folder_path) not in processed:
                    node = AsyncFileSystemNode(folder_path)
                    # Use deep strategy to ensure parent includes children
                    timestamp_adapter.strategy = 'deep'
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
                 verbose: int = 0, strict: bool = False):
        """
        Initialize folder-only strategy.
        
        Args:
            exclusion_filter: Filter for excluding files/folders
            verbose: Verbosity level
            strict: If True, exit on permission errors; if False, continue with warnings
        """
        super().__init__(exclusion_filter, verbose, strict)
    
    def _build_adapter_stack(self):
        """Build adapter stack for folder-only processing."""
        # Base filesystem adapter with conservative settings
        base = AsyncFileSystemAdapter(
            max_concurrent=25,  # Moderate concurrency
            batch_size=128,     # Medium batches
            follow_symlinks=False
        )
        
        # Wrap with error handling using our policy
        error_handled = ErrorHandlingAdapter(base, self.error_policy)
        
        # Add shallow timestamp calculation (folder-only) with exclusion filter
        timestamp = TimestampCalculationAdapter(
            error_handled, 
            strategy='shallow',
            exclusion_filter=self.exclusion_filter
        )
        
        # Add lightweight caching
        cache = create_cache_adapter(timestamp, max_memory_mb=25)

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
                        try:
                            # Wrap property access in try-except since it bypasses adapters
                            if not node.path.is_dir():
                                continue
                            if self.exclusion_filter.should_exclude(node.path, is_dir=True):
                                continue
                                
                            # Get timestamp from our timestamp adapter
                            timestamp_adapter = self._get_timestamp_adapter()
                            if timestamp_adapter:
                                timestamp = await timestamp_adapter.calculate_timestamp(node)
                            else:
                                # Fallback - should not happen
                                timestamp = datetime.fromtimestamp(node.path.stat().st_mtime)
                            
                            results.append((node.path, timestamp))
                        except (PermissionError, OSError) as e:
                            # Handle permission errors for inaccessible paths
                            if self.verbose >= 2:
                                print(f"WARNING: Skipping inaccessible path '{node.path}': {e}")
                            continue
                
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
                   verbose: int = 0, strict: bool = False) -> DazzleStrategy:
    """
    Create a DazzleTreeLib strategy instance.
    
    Args:
        strategy_type: 'standard', 'low-memory', 'tree', or 'folder-only'
        scan_strategy: 'shallow', 'deep', or 'smart' (for applicable strategies)
        exclusion_filter: Filter for excluding files/folders
        verbose: Verbosity level
        strict: If True, exit on permission errors; if False, continue with warnings
    
    Returns:
        Strategy instance
    """
    if strategy_type == 'standard':
        return StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
    elif strategy_type == 'low-memory':
        return LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
    elif strategy_type == 'tree':
        return TreeDazzleStrategy(exclusion_filter, verbose, strict)
    elif strategy_type == 'folder-only':
        return FolderOnlyDazzleStrategy(exclusion_filter, verbose, strict)
    else:
        # Default to standard
        return StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)


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
    def create_strategy(analyze_param: str, scanner, scan_strategy: str = 'shallow', strict: bool = False) -> DazzleStrategy:
        """
        Create an analysis strategy from parameter string.
        
        Args:
            analyze_param: Strategy parameter from --analyze flag
                Examples: 'auto', 'auto=2.0', 'standard,no-cache', 'low-memory'
            scanner: FolderScanner instance (for compatibility - gets exclusion filter)
            scan_strategy: Scan strategy ('shallow', 'deep', 'smart')
            strict: If True, exit on permission errors; if False, continue with warnings
        
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
            strategy = TreeDazzleStrategy(exclusion_filter, verbose, strict)
        elif primary == 'folder-only' or primary == 'folders':
            strategy = FolderOnlyDazzleStrategy(exclusion_filter, verbose, strict)
        elif primary == 'low-memory' or force_low_memory:
            strategy = LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
        elif primary == 'auto':
            # Check if low-memory modifier is present
            if force_low_memory:
                strategy = LowMemoryDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
            else:
                # Auto strategy: use standard for now (could be smarter)
                # TODO: Implement proper auto-selection based on file count
                strategy = StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
        else:
            # Default to standard
            strategy = StandardDazzleStrategy(scan_strategy, exclusion_filter, verbose, strict)
        
        return strategy
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """Return list of available strategy names."""
        return ['auto', 'standard', 'low-memory', 'tree', 'folder-only']