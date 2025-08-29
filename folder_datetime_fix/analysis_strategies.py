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
    """Tree-based strategy with in-memory n-ary tree structure."""
    
    def __init__(self, scanner: FolderScanner):
        """
        Initialize tree strategy.
        
        Args:
            scanner: FolderScanner instance
        """
        super().__init__(scanner)
        self.tree = None
    
    @trace
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        """Build tree structure and analyze."""
        # For now, fall back to standard until tree implementation is complete
        # TODO: Implement actual tree building and analysis
        return self.scanner.scan_and_collect(
            base_path,
            depths,
            strategy='deep',
            use_max_depth_detection=True
        )
    
    def get_name(self) -> str:
        return "tree"
    
    def get_description(self) -> str:
        return "Tree-based analysis with n-ary structure (future enhancement)"


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
        return ['auto', 'standard', 'low-memory', 'tree']