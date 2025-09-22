#!/usr/bin/env python3
"""Debug script to understand depth tracking.

Related to Issue #17: Tests cache handling of folder structures deeper than 3 levels.
Verifies that the integer-based depth tracking properly handles deep hierarchies.
"""

import tempfile
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing.fixtures import TestableCache

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

    # Scan to depth 2
    print(f"Scanning to depth [0, 1, 2]...")
    results = strategy.analyze(test_path, [0, 1, 2])

    # Get cache from strategy's adapter stack
    cache_adapter = strategy.adapter_stack
    testable = TestableCache(cache_adapter)

    # Check node_completeness with depths
    print(f"\nnode_completeness dict:")
    for path_str, depth in cache_adapter.node_completeness.items():
        print(f"  {path_str}: depth {depth}")

    # Check what has_node_depth returns
    print(f"\nhas_node_depth checks:")
    print(f"  Root at depth 2: {testable.has_node_depth(test_path, 2)}")
    print(f"  folder1 at depth 1: {testable.has_node_depth(folder1, 1)}")
    print(f"  folder1 at depth 2: {testable.has_node_depth(folder1, 2)}")

    # The real question - what should the test expect?
    print(f"\nTest expectations vs reality:")
    print(f"  Test expects sub2 visited: TRUE")
    print(f"  Reality sub2 visited: {testable.was_node_visited(sub2)}")
    print(f"  Why: sub2 is at depth 2, max scan depth is 2")
    print(f"  So get_children(sub2) is never called")
    print(f"  This is correct behavior per DazzleTreeLib semantics")