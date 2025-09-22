#!/usr/bin/env python3
"""Debug script to understand why node tracking isn't working.

Related to Issue #17: Investigates cache node tracking behavior.
Used to debug why certain nodes weren't being properly tracked in the cache.
"""

import tempfile
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing.fixtures import TestableCache
import dazzletreelib

print(f"DazzleTreeLib version: {dazzletreelib.__version__}")
print(f"DazzleTreeLib location: {dazzletreelib.__file__}")

# Create test structure
with tempfile.TemporaryDirectory() as tmpdir:
    test_path = Path(tmpdir)

    # Create the same structure as the test
    folder1 = test_path / 'folder1'
    folder1.mkdir()

    sub1 = folder1 / 'sub1'
    sub1.mkdir()

    sub2 = folder1 / 'sub2'
    sub2.mkdir()

    folder2 = test_path / 'folder2'
    folder2.mkdir()

    # Create strategy
    strategy = FolderOnlyDazzleStrategy(verbose=0)

    # Check adapter configuration
    print(f"\nAdapter stack type: {type(strategy.adapter_stack)}")
    print(f"Adapter stack: {strategy.adapter_stack}")

    # Check if it's a CompletenessAwareCacheAdapter
    from dazzletreelib.aio.adapters.cache_completeness_adapter import CompletenessAwareCacheAdapter
    if isinstance(strategy.adapter_stack, CompletenessAwareCacheAdapter):
        adapter = strategy.adapter_stack
        print(f"\nAdapter configuration:")
        print(f"  enable_oom_protection: {adapter.enable_oom_protection}")
        print(f"  should_track_nodes: {adapter.should_track_nodes}")
        print(f"  _track_node_visit_impl: {adapter._track_node_visit_impl}")
        if adapter._track_node_visit_impl:
            print(f"  _track_node_visit_impl name: {adapter._track_node_visit_impl.__name__}")

    # Scan to depth 2
    print(f"\nScanning to depth 2...")
    results = strategy.analyze(test_path, [0, 1, 2])

    # Get cache from strategy's adapter stack
    cache_adapter = strategy.adapter_stack
    testable = TestableCache(cache_adapter)

    # Check node_completeness
    print(f"\nnode_completeness dict: {cache_adapter.node_completeness}")
    print(f"Number of tracked nodes: {len(cache_adapter.node_completeness)}")

    # Check specific nodes
    print(f"\nNode tracking results:")
    print(f"  Root visited: {testable.was_node_visited(test_path)}")
    print(f"  folder1 visited: {testable.was_node_visited(folder1)}")
    print(f"  folder2 visited: {testable.was_node_visited(folder2)}")
    print(f"  sub1 visited: {testable.was_node_visited(sub1)}")
    print(f"  sub2 visited: {testable.was_node_visited(sub2)}")

    # Get summary
    summary = testable.get_summary()
    print(f"\nTestableCache summary: {summary}")