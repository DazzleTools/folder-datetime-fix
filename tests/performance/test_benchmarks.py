#!/usr/bin/env python3
"""
Performance benchmarks for folder_datetime_fix.

This module tests the performance of different scanning strategies
and caching mechanisms.
"""

import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from folder_datetime_fix.folder_scanner_dazzle import DazzleTreeScanner
from folder_datetime_fix.analysis_strategies_dazzle import (
    StandardDazzleStrategy,
    LowMemoryDazzleStrategy,
    TreeDazzleStrategy,
    FolderOnlyDazzleStrategy,
    create_strategy
)
from folder_datetime_fix.exclusion_filter import ExclusionFilter

from .base import PerformanceTest, BenchmarkResult
from .fixtures import (
    create_test_tree, 
    cleanup_test_tree,
    SMALL_TREE, 
    MEDIUM_TREE, 
    LARGE_TREE,
    DEEP_TREE,
    WIDE_TREE,
    SYSTEM_FILES_TREE
)
from .metrics import MetricsCollector, PerformanceMetrics


class FolderDateTimeBenchmark(PerformanceTest):
    """Benchmarks for folder_datetime_fix performance."""
    
    def __init__(self, verbose: int = 1):
        """Initialize benchmark suite."""
        super().__init__(verbose)
        self.collector = MetricsCollector()
        self.test_trees = {}
    
    def setup(self):
        """Set up test trees for benchmarking."""
        if self.verbose >= 1:
            print("Setting up test trees...")
        
        configs = {
            'small': SMALL_TREE,
            'medium': MEDIUM_TREE,
            'large': LARGE_TREE,
            'deep': DEEP_TREE,
            'wide': WIDE_TREE,
            'system': SYSTEM_FILES_TREE,
        }
        
        for name, config in configs.items():
            tree = create_test_tree(config=config)
            self.test_trees[name] = tree
            if self.verbose >= 2:
                print(f"  Created {name} tree: {tree.total_folders} folders, {tree.total_files} files")
    
    def teardown(self):
        """Clean up test trees."""
        if self.verbose >= 1:
            print("Cleaning up test trees...")
        
        for tree in self.test_trees.values():
            cleanup_test_tree(tree)
        
        self.test_trees.clear()
    
    def benchmark_strategy(
        self, 
        strategy_name: str,
        scan_type: str,
        tree_name: str = 'medium',
        depths: Optional[List[int]] = None
    ) -> BenchmarkResult:
        """
        Benchmark a specific strategy.
        
        Args:
            strategy_name: Strategy to use (standard, low-memory, tree, folder-only)
            scan_type: Scan type (shallow, deep, smart)
            tree_name: Which test tree to use
            depths: Depths to scan (default: [0,1,2])
            
        Returns:
            BenchmarkResult
        """
        tree = self.test_trees.get(tree_name)
        if not tree:
            raise ValueError(f"Test tree '{tree_name}' not found")
        
        if depths is None:
            depths = [0, 1, 2]
        
        # Create strategy
        exclusion_filter = ExclusionFilter.from_legacy(skip_generated=True)
        strategy = create_strategy(strategy_name, scan_type, exclusion_filter, verbose=0)
        
        # Create metrics
        metrics = self.collector.start_collection()
        metrics.strategy_name = f"{strategy_name}-{scan_type}"
        metrics.tree_depth = tree.config.depth
        metrics.tree_width = tree.config.width
        
        # Run benchmark
        def run_scan():
            start = time.perf_counter()
            # Use tree.path for the actual Path object
            results = strategy.analyze(tree.path if hasattr(tree, 'path') else tree, depths)
            end = time.perf_counter()
            
            metrics.total_time = end - start
            metrics.folders_scanned = len(results)
            
            # Try to extract cache statistics
            self.collector.extract_from_scanner(strategy)
            
            return results
        
        result = self.run_benchmark(
            name=f"{strategy_name}-{scan_type}-{tree_name}",
            func=run_scan,
            items_count=tree.total_folders,
            metadata={
                'strategy': strategy_name,
                'scan_type': scan_type,
                'tree': tree_name,
                'depths': depths
            }
        )
        
        self.collector.finish_collection()
        return result
    
    def benchmark_cache_effectiveness(self) -> List[BenchmarkResult]:
        """
        Benchmark cache effectiveness by running same scan twice.
        
        Returns:
            List of results [first_run, second_run]
        """
        tree_name = 'large'
        depths = list(range(4))
        
        # Use standard strategy with deep scan for maximum cache usage
        exclusion_filter = ExclusionFilter.from_legacy(skip_generated=True)
        strategy = StandardDazzleStrategy('deep', exclusion_filter, verbose=0)
        
        results = []
        
        # First run (cold cache)
        if self.verbose >= 1:
            print("\nBenchmarking cache effectiveness...")
            print("  First run (cold cache)...")
        
        result1 = self.run_benchmark(
            name=f"cache-cold-{tree_name}",
            func=lambda: strategy.analyze(self.test_trees[tree_name], depths),
            items_count=self.test_trees[tree_name].total_folders,
            metadata={'run': 'cold', 'tree': tree_name}
        )
        results.append(result1)
        
        # Second run (warm cache)
        if self.verbose >= 1:
            print("  Second run (warm cache)...")
        
        result2 = self.run_benchmark(
            name=f"cache-warm-{tree_name}",
            func=lambda: strategy.analyze(self.test_trees[tree_name], depths[:2]),  # Subset of depths
            items_count=self.test_trees[tree_name].total_folders,
            metadata={'run': 'warm', 'tree': tree_name}
        )
        results.append(result2)
        
        # Calculate cache effectiveness
        if self.verbose >= 1:
            improvement = self.compare_results(result1, result2)
            print(f"\n  Cache effectiveness:")
            print(f"    Time improvement: {improvement.get('time_improvement', 0):.1f}%")
            print(f"    Throughput improvement: {improvement.get('throughput_improvement', 0):.1f}%")
        
        return results
    
    def benchmark_scaling(self) -> List[BenchmarkResult]:
        """
        Benchmark how performance scales with tree size.
        
        Returns:
            List of results for different tree sizes
        """
        results = []
        tree_sizes = ['small', 'medium', 'large']
        
        if self.verbose >= 1:
            print("\nBenchmarking scaling behavior...")
        
        for tree_name in tree_sizes:
            result = self.benchmark_strategy(
                strategy_name='standard',
                scan_type='deep',
                tree_name=tree_name,
                depths=[0, 1, 2]
            )
            results.append(result)
        
        # Analyze scaling
        if self.verbose >= 1 and len(results) >= 2:
            print("\n  Scaling analysis:")
            for i in range(1, len(results)):
                prev = results[i-1]
                curr = results[i]
                size_ratio = curr.items_processed / prev.items_processed
                time_ratio = curr.duration / prev.duration
                print(f"    {tree_sizes[i]} vs {tree_sizes[i-1]}:")
                print(f"      Size increase: {size_ratio:.1f}x")
                print(f"      Time increase: {time_ratio:.1f}x")
                print(f"      Scaling factor: {time_ratio/size_ratio:.2f}")
    
        return results
    
    def benchmark_all_strategies(self) -> List[BenchmarkResult]:
        """
        Benchmark all available strategies.
        
        Returns:
            List of all benchmark results
        """
        strategies = ['standard', 'low-memory', 'tree', 'folder-only']
        scan_types = ['shallow', 'deep', 'smart']
        results = []
        
        if self.verbose >= 1:
            print("\nBenchmarking all strategies...")
        
        for strategy in strategies:
            # Skip invalid combinations
            if strategy == 'tree' and scan_types[0] in ['shallow', 'smart']:
                # Tree strategy only supports deep scan internally
                scan_types_to_test = ['deep']
            elif strategy == 'folder-only':
                # Folder-only uses its own scan approach
                scan_types_to_test = ['shallow']
            else:
                scan_types_to_test = scan_types
            
            for scan_type in scan_types_to_test:
                try:
                    result = self.benchmark_strategy(
                        strategy_name=strategy,
                        scan_type=scan_type,
                        tree_name='medium',
                        depths=[0, 1, 2]
                    )
                    results.append(result)
                except Exception as e:
                    if self.verbose >= 1:
                        print(f"  Skipped {strategy}-{scan_type}: {e}")
        
        return results
    
    def run_full_benchmark_suite(self):
        """Run the complete benchmark suite."""
        print("=" * 60)
        print("FOLDER DATETIME FIX PERFORMANCE BENCHMARKS")
        print("=" * 60)
        
        try:
            # Setup
            self.setup()
            
            # Run benchmarks
            print("\n1. Strategy Comparison")
            print("-" * 40)
            self.benchmark_all_strategies()
            
            print("\n2. Cache Effectiveness")
            print("-" * 40)
            self.benchmark_cache_effectiveness()
            
            print("\n3. Scaling Behavior")
            print("-" * 40)
            self.benchmark_scaling()
            
            # Print summary
            self.print_summary()
            
            # Save metrics
            metrics_file = Path("performance_metrics.json")
            self.collector.save_to_file(metrics_file)
            print(f"\nMetrics saved to: {metrics_file}")
            
        finally:
            # Cleanup
            self.teardown()


def main():
    """Run benchmarks from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance benchmarks for folder_datetime_fix")
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='Increase verbosity (can be repeated)')
    parser.add_argument('--quick', action='store_true',
                        help='Run quick benchmark subset')
    parser.add_argument('--strategy', choices=['standard', 'low-memory', 'tree', 'folder-only'],
                        help='Benchmark specific strategy')
    parser.add_argument('--tree', choices=['small', 'medium', 'large', 'deep', 'wide', 'system'],
                        default='medium', help='Test tree size')
    
    args = parser.parse_args()
    
    benchmark = FolderDateTimeBenchmark(verbose=args.verbose)
    
    if args.quick:
        # Quick benchmark
        print("Running quick benchmark...")
        benchmark.setup()
        try:
            result = benchmark.benchmark_strategy('standard', 'deep', args.tree)
            print(f"\n{result}")
        finally:
            benchmark.teardown()
    
    elif args.strategy:
        # Benchmark specific strategy
        print(f"Benchmarking {args.strategy} strategy...")
        benchmark.setup()
        try:
            for scan_type in ['shallow', 'deep', 'smart']:
                try:
                    result = benchmark.benchmark_strategy(args.strategy, scan_type, args.tree)
                    print(f"\n{result}")
                except Exception as e:
                    print(f"Skipped {scan_type}: {e}")
        finally:
            benchmark.teardown()
    
    else:
        # Full suite
        benchmark.run_full_benchmark_suite()


if __name__ == '__main__':
    main()