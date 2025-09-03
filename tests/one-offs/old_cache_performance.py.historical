#!/usr/bin/env python
"""
Quick test to verify cache performance improvement.
"""

import tempfile
import shutil
import time
from pathlib import Path

# Add parent dir to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from folder_datetime_fix.folder_scanner import FolderScanner


def create_test_tree(base_path, depth=5, width=3):
    """Create a test directory tree."""
    def create_level(path, current_depth):
        if current_depth >= depth:
            return
        
        # Create files at this level
        for i in range(3):
            file_path = path / f"file_{current_depth}_{i}.txt"
            file_path.write_text(f"Test file at depth {current_depth}")
        
        # Create subdirectories
        for i in range(width):
            subdir = path / f"folder_{current_depth}_{i}"
            subdir.mkdir(exist_ok=True)
            create_level(subdir, current_depth + 1)
    
    create_level(base_path, 0)


def test_cache_performance():
    """Test that caching improves performance."""
    # Create test directory
    test_dir = Path(tempfile.mkdtemp(prefix='cache_perf_'))
    
    try:
        print("Creating test tree...")
        create_test_tree(test_dir, depth=4, width=3)
        
        # Test with cache disabled
        print("\nTesting WITHOUT cache:")
        scanner_no_cache = FolderScanner(skip_generated=True, verbose=0, use_cache=False)
        
        start = time.time()
        results = scanner_no_cache.scan_and_collect(test_dir, list(range(5)), strategy='deep')
        time_no_cache = time.time() - start
        
        print(f"  Processed {len(results)} folders in {time_no_cache:.3f} seconds")
        
        # Test with cache enabled
        print("\nTesting WITH cache:")
        scanner_with_cache = FolderScanner(skip_generated=True, verbose=0, use_cache=True)
        
        start = time.time()
        results = scanner_with_cache.scan_and_collect(test_dir, list(range(5)), strategy='deep')
        time_with_cache = time.time() - start
        
        print(f"  Processed {len(results)} folders in {time_with_cache:.3f} seconds")
        
        # Get cache statistics
        if scanner_with_cache.cache:
            stats = scanner_with_cache.cache.get_statistics()
            print(f"\nCache Statistics:")
            print(f"  Hits: {stats['hits']}")
            print(f"  Misses: {stats['misses']}")
            print(f"  Hit Rate: {stats['hit_rate']:.1%}")
            print(f"  Entries: {stats['entries']}")
            print(f"  Memory: {stats['memory_bytes']:,} bytes")
        
        # Calculate improvement
        if time_no_cache > 0:
            improvement = (time_no_cache - time_with_cache) / time_no_cache * 100
            print(f"\nPerformance improvement: {improvement:.1f}%")
            
            # Note: First run with cache might be slower due to cache population
            # Real benefits come from subsequent operations
            print("\nRunning second scan to show cache benefits...")
            start = time.time()
            results2 = scanner_with_cache.scan_and_collect(test_dir, list(range(3)), strategy='deep')
            time_cached = time.time() - start
            print(f"  Second scan: {len(results2)} folders in {time_cached:.3f} seconds")
            
            if scanner_with_cache.cache:
                stats = scanner_with_cache.cache.get_statistics()
                print(f"  Hit Rate after second scan: {stats['hit_rate']:.1%}")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    test_cache_performance()