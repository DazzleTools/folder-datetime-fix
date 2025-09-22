#!/usr/bin/env python3
"""Demonstrate correct cache expectations."""

import tempfile
import shutil
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing import TestableCache

# Create test structure
test_dir = tempfile.mkdtemp(prefix='test_cache_')
test_path = Path(test_dir)

try:
    # Create folder structure
    (test_path / 'folder1').mkdir()
    (test_path / 'folder2').mkdir()
    (test_path / 'folder1' / 'sub1').mkdir()
    
    strategy = FolderOnlyDazzleStrategy(verbose=0)
    
    # First run - populates cache
    results1 = strategy.analyze(test_path, [0, 1])
    print(f"Found {len(results1)} folders")
    
    cache_adapter = strategy.adapter_stack
    testable = TestableCache(cache_adapter)
    
    print("\n=== WRONG EXPECTATION (what tests currently do) ===")
    # Tests expect each result folder to be a cache key
    for path, _ in results1:
        cached = testable.was_path_cached(path)
        print(f"  {path.name}: cached={cached}")
    
    print("\n=== CORRECT EXPECTATION (how cache actually works) ===")
    # Cache stores parent->children mappings
    # Only parents that were queried for children are cache keys
    
    # Root is definitely cached (we asked for its children at depth 0)
    print(f"  Root ({test_path.name}): cached={testable.was_path_cached(test_path)}")
    
    # Folders at depth 1 are only cached if we asked for THEIR children
    # Since we only went to depth 1, we didn't ask for folder1's children
    folder1 = test_path / 'folder1'
    print(f"  folder1: cached={testable.was_path_cached(folder1)}")
    
    print("\n=== Cache Summary ===")
    summary = testable.get_summary()
    print(f"Total cache entries: {summary['total_entries']}")
    print(f"  - Shallow: {summary['shallow_count']}")
    print(f"  - Complete: {summary['complete_count']}")
    
    print("\n=== What's Actually in the Cache ===")
    if hasattr(cache_adapter, 'cache'):
        for key in cache_adapter.cache.keys():
            print(f"  Key: {key}")

finally:
    shutil.rmtree(test_dir, ignore_errors=True)