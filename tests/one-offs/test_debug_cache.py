#!/usr/bin/env python3
"""Debug cache behavior."""

import tempfile
import shutil
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing import TestableCache

# Create test structure
test_dir = tempfile.mkdtemp(prefix='test_cache_')
test_path = Path(test_dir)

try:
    # Create some folders
    (test_path / 'folder1').mkdir()
    (test_path / 'folder2').mkdir()
    (test_path / 'folder1' / 'sub1').mkdir()
    
    # Create strategy
    strategy = FolderOnlyDazzleStrategy(verbose=1)
    
    print(f"Test path: {test_path}")
    print(f"Adapter stack type: {type(strategy.adapter_stack)}")
    print(f"Has cache attr: {hasattr(strategy.adapter_stack, 'cache')}")
    print(f"Has _cache attr: {hasattr(strategy.adapter_stack, '_cache')}")
    
    # First run
    print("\n=== First run ===")
    results1 = strategy.analyze(test_path, [0, 1])
    print(f"Results: {len(results1)} folders found")
    
    # Check cache
    cache_adapter = strategy.adapter_stack
    if hasattr(cache_adapter, 'cache'):
        print(f"Cache entries: {len(cache_adapter.cache)}")
        for key, value in list(cache_adapter.cache.items())[:3]:
            print(f"  Key: {key}")
            print(f"  Value type: {type(value)}")
            if hasattr(value, 'completeness'):
                print(f"  Completeness: {value.completeness}")
    
    # Check with TestableCache
    testable = TestableCache(cache_adapter)
    summary = testable.get_summary()
    print(f"\nTestableCache summary: {summary}")
    
    # Test specific path
    if results1:
        test_path_result = results1[0][0]
        print(f"\nTesting path: {test_path_result}")
        print(f"  was_path_cached: {testable.was_path_cached(test_path_result)}")
        print(f"  get_completeness: {testable.get_completeness(test_path_result)}")
        print(f"  verify_cache_reuse: {testable.verify_cache_reuse(test_path_result)}")

finally:
    shutil.rmtree(test_dir, ignore_errors=True)