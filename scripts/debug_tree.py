#!/usr/bin/env python3
"""
Debug tool for visualizing TreeStrategy and cache state.
Shows what's actually in memory, including partial processing and cache completeness.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_datetime_fix.folder_scanner import FolderScanner
from folder_datetime_fix.analysis_strategies import TreeStrategy, StandardStrategy
from folder_datetime_fix.cache import CacheCompleteness


class TreeDebugger:
    """Debug and visualize tree structures and cache state."""
    
    # Visual indicators for processing state
    SYMBOLS = {
        'folder_complete': '[DIR+]',      # Fully processed folder
        'folder_partial': '[DIR~]',        # Partially processed folder
        'folder_unprocessed': '[DIR ]',    # Not processed
        'folder_cached': '[DIR$]',         # In cache
        'folder_error': '[DIR!]',          # Error during processing
        'tree_branch': '+-- ',
        'tree_last': '`-- ',
        'tree_pipe': '|   ',
        'tree_space': '    '
    }
    
    def __init__(self, scanner: Optional[FolderScanner] = None):
        """Initialize debugger with optional scanner."""
        self.scanner = scanner or FolderScanner(verbose=0)
        self.cache_stats = {}
        
    def visualize_tree_strategy(self, base_path: Path, depths: List[int],
                               show_cache: bool = True) -> str:
        """
        Visualize TreeStrategy's internal node structure.
        
        Args:
            base_path: Root path to analyze
            depths: Depth levels to process (e.g., [0, 1, 2])
            show_cache: Show cache completeness info
            
        Returns:
            Visual representation of tree structure
        """
        output = []
        output.append("TREE STRATEGY VISUALIZATION")
        output.append("=" * 60)
        output.append(f"Path: {base_path}")
        output.append(f"Requested depths: {depths}")
        output.append("")
        
        # Create and run TreeStrategy
        strategy = TreeStrategy(self.scanner)
        
        # Analyze
        results = strategy.analyze(base_path, depths)
        
        # Visualize the tree structure
        if strategy.root:
            output.append("Tree Structure in Memory:")
            output.append("-" * 40)
            self._visualize_node(strategy.root, output, "", depths, show_cache)
        else:
            output.append("No tree structure built")
        
        # Show statistics
        output.append("")
        output.append("=" * 60)
        output.append("MEMORY STATISTICS")
        output.append("=" * 60)
        
        # Count nodes
        total_nodes = self._count_nodes(strategy.root) if strategy.root else 0
        processed_nodes = sum(1 for _, ts in results if ts is not None)
        
        output.append(f"Total nodes in tree: {total_nodes}")
        output.append(f"Nodes at requested depths: {len(results)}")
        output.append(f"Nodes with timestamps: {processed_nodes}")
        
        # Estimate memory usage
        bytes_per_node = 200  # From our design
        memory_kb = (total_nodes * bytes_per_node) / 1024
        output.append(f"Estimated memory usage: {memory_kb:.1f} KB")
        
        # Cache statistics if enabled
        if show_cache and self.scanner.cache:
            output.append("")
            output.append("CACHE STATISTICS")
            output.append("-" * 40)
            stats = self.scanner.cache.get_statistics()
            output.append(f"Cache entries: {stats['entries']}")
            output.append(f"Cache hits: {stats['hits']}")
            output.append(f"Cache misses: {stats['misses']}")
            output.append(f"Hit rate: {stats['hit_rate']:.1%}")
            
        return "\n".join(output)
    
    def _visualize_node(self, node, output: List[str], prefix: str,
                       requested_depths: List[int], show_cache: bool):
        """Recursively visualize tree nodes."""
        # Determine node state
        is_requested = node.depth in requested_depths
        is_calculated = node.is_calculated
        has_timestamp = node.computed_mtime is not None
        
        # Choose symbol
        if is_calculated and has_timestamp:
            symbol = self.SYMBOLS['folder_complete']
        elif is_calculated:
            symbol = self.SYMBOLS['folder_partial']
        else:
            symbol = self.SYMBOLS['folder_unprocessed']
        
        # Check cache state
        cache_info = ""
        if show_cache and self.scanner.cache and hasattr(self.scanner.cache, 'cache'):
            # Access the internal cache dictionary
            cache_dict = self.scanner.cache.cache
            entry = cache_dict.get(str(node.full_path))
            if entry:
                completeness = entry.completeness
                if completeness == CacheCompleteness.COMPLETE:
                    cache_info = " [CACHE: Complete]"
                elif completeness == CacheCompleteness.SHALLOW:
                    cache_info = " [CACHE: Shallow]"
                elif completeness == CacheCompleteness.DEEP_NO_RECURSIVE:
                    cache_info = " [CACHE: Deep-no-recurse]"
        
        # Build line
        line = f"{prefix}{symbol} {node.name}"
        
        # Add depth info
        line += f" (d={node.depth}"
        
        # Add processing info
        if is_requested:
            line += ", REQUESTED"
        if not is_calculated:
            line += ", NOT PROCESSED"
        
        line += ")"
        
        # Add timestamp if available
        if has_timestamp and node.computed_mtime:
            ts_str = node.computed_mtime.strftime('%Y-%m-%d %H:%M:%S')
            line += f" [{ts_str}]"
        elif is_calculated:
            line += " [No timestamp]"
        
        # Add cache info
        line += cache_info
        
        output.append(line)
        
        # Recurse for children
        for i, child in enumerate(node.children):
            is_last = i == len(node.children) - 1
            
            # Determine if we should show this branch
            # Show if: child is at requested depth OR has descendants at requested depth
            should_show = (child.depth in requested_depths or 
                          self._has_requested_descendants(child, requested_depths))
            
            if should_show:
                child_prefix = prefix
                if is_last:
                    child_prefix += self.SYMBOLS['tree_last']
                    next_prefix = prefix + self.SYMBOLS['tree_space']
                else:
                    child_prefix += self.SYMBOLS['tree_branch']
                    next_prefix = prefix + self.SYMBOLS['tree_pipe']
                
                # Show child
                self._visualize_node(child, output, next_prefix,
                                   requested_depths, show_cache)
            else:
                # Indicate pruned branch
                if i == 0:  # Only show once
                    output.append(f"{prefix}... ({len(node.children)} children not at requested depths)")
                    break
    
    def _has_requested_descendants(self, node, requested_depths: List[int]) -> bool:
        """Check if node has any descendants at requested depths."""
        for child in node.children:
            if child.depth in requested_depths:
                return True
            if self._has_requested_descendants(child, requested_depths):
                return True
        return False
    
    def _count_nodes(self, node) -> int:
        """Count total nodes in tree."""
        if not node:
            return 0
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def compare_strategies(self, base_path: Path, depths: List[int]) -> str:
        """
        Compare different strategies' memory and processing.
        
        Args:
            base_path: Root path to analyze
            depths: Depth levels to process
            
        Returns:
            Comparison visualization
        """
        output = []
        output.append("STRATEGY COMPARISON")
        output.append("=" * 60)
        output.append(f"Path: {base_path}")
        output.append(f"Depths: {depths}")
        output.append("")
        
        # Test each strategy
        strategies = [
            ('StandardStrategy', StandardStrategy(self.scanner)),
            ('TreeStrategy', TreeStrategy(self.scanner))
        ]
        
        for name, strategy in strategies:
            output.append(f"\n{name}:")
            output.append("-" * 40)
            
            # Time the analysis
            import time
            start = time.time()
            results = strategy.analyze(base_path, depths)
            elapsed = time.time() - start
            
            output.append(f"Time: {elapsed:.3f} seconds")
            output.append(f"Results: {len(results)} folders")
            
            # Count timestamps
            with_ts = sum(1 for _, ts in results if ts is not None)
            output.append(f"With timestamps: {with_ts}")
            
            # Memory estimate
            if hasattr(strategy, 'root'):  # TreeStrategy
                nodes = self._count_nodes(strategy.root) if strategy.root else 0
                memory = (nodes * 200) / 1024
                output.append(f"Tree nodes: {nodes}")
                output.append(f"Memory: ~{memory:.1f} KB")
            elif self.scanner.cache:  # StandardStrategy with cache
                entries = len(self.scanner.cache.cache) if hasattr(self.scanner.cache, 'cache') else 0
                memory = (entries * 350) / 1024
                output.append(f"Cache entries: {entries}")
                output.append(f"Memory: ~{memory:.1f} KB")
        
        return "\n".join(output)
    
    def visualize_cache_completeness(self, base_path: Path, depths: List[int]) -> str:
        """
        Visualize cache completeness levels after analysis.
        
        Args:
            base_path: Root path
            depths: Depths to analyze
            
        Returns:
            Cache completeness visualization
        """
        output = []
        output.append("CACHE COMPLETENESS VISUALIZATION")
        output.append("=" * 60)
        
        # Enable cache
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = StandardStrategy(scanner)
        
        # Run analysis
        results = strategy.analyze(base_path, depths)
        
        if not scanner.cache or not hasattr(scanner.cache, 'cache'):
            output.append("No cache data available")
            return "\n".join(output)
        
        # Group cache entries by completeness
        by_completeness = {
            CacheCompleteness.COMPLETE: [],
            CacheCompleteness.DEEP_NO_RECURSIVE: [],
            CacheCompleteness.SHALLOW: [],
            CacheCompleteness.FROM_DEPTH: []
        }
        
        for path_str, entry in scanner.cache.cache.items():
            completeness = entry.completeness
            by_completeness[completeness].append((path_str, entry))
        
        # Display by completeness level
        for level in [CacheCompleteness.COMPLETE,
                     CacheCompleteness.DEEP_NO_RECURSIVE,
                     CacheCompleteness.SHALLOW,
                     CacheCompleteness.FROM_DEPTH]:
            
            entries = by_completeness[level]
            if entries:
                output.append(f"\n{level.name}: {len(entries)} entries")
                output.append("-" * 40)
                
                # Show first few entries
                for path_str, entry in entries[:5]:
                    path = Path(path_str)
                    rel_path = path.relative_to(base_path) if base_path in path.parents else path
                    
                    line = f"  [DIR] {rel_path}"
                    
                    if entry.timestamp:
                        line += f" [{entry.timestamp.strftime('%H:%M:%S')}]"
                    
                    # Show what depths this entry satisfies
                    if hasattr(entry, 'satisfied_depths') and entry.satisfied_depths:
                        line += f" (satisfies depths: {sorted(entry.satisfied_depths)})"
                    
                    output.append(line)
                
                if len(entries) > 5:
                    output.append(f"  ... and {len(entries) - 5} more")
        
        # Summary
        output.append("")
        output.append("=" * 60)
        output.append("SUMMARY")
        output.append("-" * 40)
        
        total = sum(len(entries) for entries in by_completeness.values())
        output.append(f"Total cache entries: {total}")
        
        if total > 0:
            complete_pct = (len(by_completeness[CacheCompleteness.COMPLETE]) / total) * 100
            output.append(f"Complete entries: {complete_pct:.1f}%")
        
        # Cache statistics
        stats = scanner.cache.get_statistics()
        output.append(f"Cache hit rate: {stats['hit_rate']:.1%}")
        
        return "\n".join(output)


def main():
    """CLI interface for tree debugging."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug tree structures and cache state')
    parser.add_argument('path', help='Path to analyze')
    parser.add_argument('--depths', '-d', type=str, default='0,1,2',
                       help='Comma-separated depth levels (default: 0,1,2)')
    parser.add_argument('--mode', '-m', choices=['tree', 'cache', 'compare'],
                       default='tree',
                       help='Visualization mode')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable cache visualization')
    
    args = parser.parse_args()
    
    # Parse depths
    depths = [int(d.strip()) for d in args.depths.split(',')]
    
    # Create debugger
    debugger = TreeDebugger()
    
    # Run visualization
    base_path = Path(args.path).resolve()
    
    if args.mode == 'tree':
        result = debugger.visualize_tree_strategy(
            base_path, depths, 
            show_cache=not args.no_cache
        )
    elif args.mode == 'cache':
        result = debugger.visualize_cache_completeness(base_path, depths)
    elif args.mode == 'compare':
        result = debugger.compare_strategies(base_path, depths)
    else:
        result = "Unknown mode"
    
    print(result)


if __name__ == '__main__':
    main()