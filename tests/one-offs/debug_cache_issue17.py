#!/usr/bin/env python3
"""Debug script to understand cache structure after Issue #17 changes."""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, os.path.abspath('../..'))

from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing import TestableCache


def main():
    """Debug cache issues with new tuple-based keys."""
    # Create test structure
    with tempfile.TemporaryDirectory(prefix='debug_cache_') as tmpdir:
        test_path = Path(tmpdir)
        
        # Create simple structure
        (test_path / 'folder1').mkdir()
        (test_path / 'folder2').mkdir()
        (test_path / 'folder1' / 'sub1').mkdir()
        (test_path / 'file.txt').write_text('test')
        
        print(f"Test directory: {test_path}")
        print("Structure created:")
        for root, dirs, files in os.walk(test_path):
            level = root.replace(str(test_path), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        # Create strategy and analyze
        strategy = FolderOnlyDazzleStrategy(verbose=2)
        print("\n=== Running analysis ===")
        results = strategy.analyze(test_path, [0, 1])
        
        print(f"\nAnalysis returned {len(results)} results")
        for path, timestamp in results[:5]:  # Show first 5
            print(f"  {path}: {timestamp}")
        
        # Get cache adapter
        cache_adapter = strategy.adapter_stack
        print(f"\nAdapter stack type: {type(cache_adapter)}")
        print(f"Has 'cache' attribute: {hasattr(cache_adapter, 'cache')}")
        
        if hasattr(cache_adapter, 'cache'):
            cache = cache_adapter.cache
            print(f"Cache type: {type(cache)}")
            print(f"Cache size: {len(cache)}")
            
            if len(cache) > 0:
                print("\nCache contents (first 5):")
                for i, (key, value) in enumerate(list(cache.items())[:5]):
                    print(f"  Key {i}: {key}")
                    print(f"    Type: {type(key)}")
                    if isinstance(key, tuple):
                        print(f"    Length: {len(key)}")
                        for j, part in enumerate(key):
                            print(f"      [{j}]: {part!r}")
                    print(f"    Value type: {type(value)}")
                    if hasattr(value, 'depth'):
                        print(f"    Depth: {value.depth}")
                    if hasattr(value, 'data'):
                        print(f"    Data: {value.data}")
        
        # Test TestableCache
        print("\n=== Testing TestableCache ===")
        testable = TestableCache(cache_adapter)
        
        summary = testable.get_summary()
        print(f"Summary: {summary}")
        
        print(f"\nwas_path_cached({test_path}): {testable.was_path_cached(test_path)}")
        print(f"was_node_visited({test_path}): {testable.was_node_visited(test_path)}")
        
        # Check if any paths are detected as cached
        for path in [test_path, test_path / 'folder1', test_path / 'folder2']:
            print(f"  {path}: cached={testable.was_path_cached(path)}, visited={testable.was_node_visited(path)}")


if __name__ == '__main__':
    main()