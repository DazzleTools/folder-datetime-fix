#!/usr/bin/env python3
"""Test to understand the cache fallback behavior.

Related to Issue #17: Created during investigation of cache depth limitations.
Tests the fallback behavior when DazzleTreeLib's cache tracking isn't available.
"""

import tempfile
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing.fixtures import TestableCache

# Create test structure
with tempfile.TemporaryDirectory() as tmpdir:
    test_path = Path(tmpdir)

    folder1 = test_path / 'folder1'
    folder1.mkdir()

    sub2 = folder1 / 'sub2'
    sub2.mkdir()

    # Create strategy
    strategy = FolderOnlyDazzleStrategy(verbose=0)

    # Scan to depth 2
    results = strategy.analyze(test_path, [0, 1, 2])

    # Get cache from strategy's adapter stack
    cache_adapter = strategy.adapter_stack
    testable = TestableCache(cache_adapter)

    # Check both methods
    print(f"sub2 path: {sub2}")
    print(f"\nNode tracking (node_completeness):")
    print(f"  was_node_visited(sub2): {testable.was_node_visited(sub2)}")
    print(f"  node_completeness: {cache_adapter.node_completeness}")

    print(f"\nCache checking:")
    print(f"  was_path_cached(sub2): {testable.was_path_cached(sub2)}")
    print(f"  Cache keys: {list(cache_adapter.cache.keys())}")

    # The key insight
    print(f"\nThe issue:")
    print(f"  Before fix: node_completeness was empty in fast mode")
    print(f"  So was_node_visited() fell back to was_path_cached()")
    print(f"  was_path_cached() returns True for sub2 because it's in the cache")
    print(f"  After fix: node_completeness works correctly")
    print(f"  So was_node_visited() returns False for sub2 (correct semantics)")
    print(f"  Test was written expecting the fallback behavior, not correct semantics")