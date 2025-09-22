#!/usr/bin/env python3
"""Analyze what 'visited' should mean for modified_datetime_fix.

Related to Issue #17: Explores semantic differences in cache tracking.
Analyzes what 'visited' vs 'discovered' vs 'expanded' means for cache completeness.
"""

import tempfile
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing.fixtures import TestableCache

# Create test structure
with tempfile.TemporaryDirectory() as tmpdir:
    test_path = Path(tmpdir)

    # Create structure:
    # root/
    #   folder1/
    #     sub1/
    #     sub2/
    #   folder2/

    folder1 = test_path / 'folder1'
    folder1.mkdir()
    (folder1 / 'file1.txt').touch()  # Add a file to folder1

    sub1 = folder1 / 'sub1'
    sub1.mkdir()
    (sub1 / 'file2.txt').touch()  # Add a file to sub1

    sub2 = folder1 / 'sub2'
    sub2.mkdir()
    (sub2 / 'file3.txt').touch()  # Add a file to sub2

    folder2 = test_path / 'folder2'
    folder2.mkdir()

    # Create strategy
    strategy = FolderOnlyDazzleStrategy(verbose=0)

    # Scan to depth 2
    print("Scanning to depths [0, 1, 2]...")
    results = strategy.analyze(test_path, [0, 1, 2])

    print(f"\nResults returned from analyze (folders with mtimes):")
    for path, mtime in results:
        depth = len(path.relative_to(test_path).parts)
        print(f"  Depth {depth}: {path.relative_to(test_path)} - mtime: {mtime is not None}")

    # Get cache from strategy's adapter stack
    cache_adapter = strategy.adapter_stack
    testable = TestableCache(cache_adapter)

    print(f"\nDazzleTreeLib node_completeness (nodes where get_children was called):")
    for path_str, depth in cache_adapter.node_completeness.items():
        p = Path(path_str)
        rel_path = p.relative_to(test_path) if p != test_path else Path('.')
        print(f"  {rel_path}: depth {depth}")

    print(f"\nKey Question for modified_datetime_fix:")
    print(f"  When scanning to depth 2, should sub2 be considered 'visited'?")
    print(f"  - sub2 IS evaluated for mtime (appears in results): {any(p == sub2 for p, _ in results)}")
    print(f"  - sub2 IS NOT expanded for children (not in node_completeness): {str(sub2) not in cache_adapter.node_completeness}")
    print(f"  - Current was_node_visited(sub2): {testable.was_node_visited(sub2)}")

    print(f"\nThe semantic mismatch:")
    print(f"  modified_datetime_fix needs: 'visited' = folder was evaluated for mtime")
    print(f"  DazzleTreeLib provides: 'visited' = get_children() was called")
    print(f"  These are different at the max depth boundary!")