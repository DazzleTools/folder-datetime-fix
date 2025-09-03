"""
Base classes for performance testing.
"""

import time
import tracemalloc
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    name: str
    duration: float  # seconds
    memory_peak: int  # bytes
    memory_current: int  # bytes
    items_processed: int
    metadata: Dict[str, Any]
    
    @property
    def items_per_second(self) -> float:
        """Calculate throughput."""
        if self.duration > 0:
            return self.items_processed / self.duration
        return 0.0
    
    @property
    def memory_per_item(self) -> float:
        """Calculate memory usage per item."""
        if self.items_processed > 0:
            return self.memory_peak / self.items_processed
        return 0.0
    
    def __str__(self) -> str:
        """Human-readable result."""
        return (
            f"{self.name}:\n"
            f"  Duration: {self.duration:.3f}s\n"
            f"  Items: {self.items_processed}\n"
            f"  Throughput: {self.items_per_second:.1f} items/s\n"
            f"  Memory Peak: {self.memory_peak / 1024 / 1024:.1f} MB\n"
            f"  Memory/Item: {self.memory_per_item / 1024:.1f} KB"
        )


class PerformanceTest:
    """Base class for performance tests."""
    
    def __init__(self, verbose: int = 0):
        """
        Initialize performance test.
        
        Args:
            verbose: Verbosity level (0=quiet, 1=summary, 2=detailed)
        """
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
    
    def measure(self, func, *args, **kwargs) -> tuple:
        """
        Measure performance of a function.
        
        Returns:
            Tuple of (result, duration, memory_peak, memory_current)
        """
        # Start memory tracking
        tracemalloc.start()
        tracemalloc.clear_traces()
        
        # Measure execution time
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Get memory statistics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration = end_time - start_time
        
        if self.verbose >= 2:
            print(f"  Execution: {duration:.3f}s, Memory: {peak/1024/1024:.1f}MB")
        
        return result, duration, peak, current
    
    def run_benchmark(
        self, 
        name: str, 
        func, 
        *args,
        items_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run a single benchmark.
        
        Args:
            name: Benchmark name
            func: Function to benchmark
            items_count: Number of items processed (for throughput calculation)
            metadata: Additional metadata to store
            *args, **kwargs: Arguments for func
            
        Returns:
            BenchmarkResult
        """
        if self.verbose >= 1:
            print(f"Running benchmark: {name}")
        
        result, duration, peak_memory, current_memory = self.measure(func, *args, **kwargs)
        
        # Try to determine items count from result if not provided
        if items_count is None:
            if hasattr(result, '__len__'):
                items_count = len(result)
            else:
                items_count = 1
        
        benchmark_result = BenchmarkResult(
            name=name,
            duration=duration,
            memory_peak=peak_memory,
            memory_current=current_memory,
            items_processed=items_count,
            metadata=metadata or {}
        )
        
        self.results.append(benchmark_result)
        
        if self.verbose >= 1:
            print(f"  Completed in {duration:.3f}s")
        
        return benchmark_result
    
    def compare_results(
        self, 
        baseline: BenchmarkResult, 
        current: BenchmarkResult
    ) -> Dict[str, float]:
        """
        Compare two benchmark results.
        
        Returns:
            Dictionary with percentage improvements (positive = better)
        """
        comparison = {}
        
        # Time improvement (less time is better)
        if baseline.duration > 0:
            time_improvement = (baseline.duration - current.duration) / baseline.duration * 100
            comparison['time_improvement'] = time_improvement
        
        # Throughput improvement (more is better)
        if baseline.items_per_second > 0:
            throughput_improvement = (
                (current.items_per_second - baseline.items_per_second) / 
                baseline.items_per_second * 100
            )
            comparison['throughput_improvement'] = throughput_improvement
        
        # Memory improvement (less is better)
        if baseline.memory_peak > 0:
            memory_improvement = (
                (baseline.memory_peak - current.memory_peak) / 
                baseline.memory_peak * 100
            )
            comparison['memory_improvement'] = memory_improvement
        
        return comparison
    
    def print_summary(self):
        """Print summary of all results."""
        if not self.results:
            print("No benchmark results available.")
            return
        
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        for result in self.results:
            print(f"\n{result}")
        
        # If we have multiple results, show comparisons
        if len(self.results) > 1:
            print("\n" + "-" * 60)
            print("COMPARISONS")
            print("-" * 60)
            
            baseline = self.results[0]
            for result in self.results[1:]:
                comparison = self.compare_results(baseline, result)
                print(f"\n{result.name} vs {baseline.name}:")
                for metric, value in comparison.items():
                    direction = "+" if value > 0 else "-"
                    print(f"  {metric}: {direction} {abs(value):.1f}%")