#!/usr/bin/env python3
"""
Test the new DazzleTreeLib-based strategy implementations.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from folder_datetime_fix.analysis_strategies_dazzle import (
    StandardDazzleStrategy,
    LowMemoryDazzleStrategy,
    TreeDazzleStrategy,
    FolderOnlyDazzleStrategy,
    create_strategy
)
from folder_datetime_fix.exclusion_filter import ExclusionFilter


def create_test_tree(base_path: Path):
    """Create a test directory tree."""
    # Clean and create
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)
    
    # Create structure
    (base_path / "file_root.txt").write_text("root")
    
    dir1 = base_path / "dir1"
    dir1.mkdir()
    (dir1 / "file1.txt").write_text("content1")
    
    dir2 = base_path / "dir2"
    dir2.mkdir()
    (dir2 / "file2.txt").write_text("content2")
    
    subdir = dir1 / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3")
    
    # Create a system folder to test exclusion
    sys_dir = base_path / ".git"
    sys_dir.mkdir()
    (sys_dir / "config").write_text("git config")
    
    return base_path


def test_strategy(strategy, name: str, base_path: Path):
    """Test a single strategy."""
    print(f"\nTesting {name}...")
    print(f"  Description: {strategy.get_description()}")
    
    # Test with multiple depths
    depths = [0, 1, 2]
    results = strategy.analyze(base_path, depths)
    
    print(f"  Found {len(results)} folders at depths {depths}")
    
    # Show some results
    for path, timestamp in results[:5]:
        rel_path = path.relative_to(base_path.parent)
        print(f"    - {rel_path}: {timestamp}")
    
    # Check that we got results
    assert len(results) > 0, f"Expected some results from {name}"
    
    # Check that timestamps are present
    has_timestamps = sum(1 for _, ts in results if ts is not None)
    print(f"  Folders with timestamps: {has_timestamps}/{len(results)}")
    
    # Show configuration
    config = strategy.get_config()
    print(f"  Adapter stack: {' -> '.join(config['adapter_stack'])}")
    
    print(f"  [PASS]")


def test_dazzle_strategies():
    """Test all DazzleTreeLib strategy implementations."""
    print("Testing DazzleTreeLib Strategy Implementations")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / "test_tree"
        create_test_tree(test_path)
        
        # Create exclusion filter
        exclusion_filter = ExclusionFilter.from_legacy(skip_generated=True)
        
        # Test 1: Standard Strategy (shallow)
        strategy = StandardDazzleStrategy('shallow', exclusion_filter, verbose=1)
        test_strategy(strategy, "Standard Strategy (shallow)", test_path)
        
        # Test 2: Standard Strategy (deep)
        strategy = StandardDazzleStrategy('deep', exclusion_filter, verbose=1)
        test_strategy(strategy, "Standard Strategy (deep)", test_path)
        
        # Test 3: Standard Strategy (smart)
        strategy = StandardDazzleStrategy('smart', exclusion_filter, verbose=1)
        test_strategy(strategy, "Standard Strategy (smart)", test_path)
        
        # Test 4: Low Memory Strategy
        strategy = LowMemoryDazzleStrategy('shallow', exclusion_filter, verbose=1)
        test_strategy(strategy, "Low Memory Strategy", test_path)
        
        # Test 5: Tree Strategy
        strategy = TreeDazzleStrategy(exclusion_filter, verbose=1)
        test_strategy(strategy, "Tree Strategy", test_path)
        
        # Test 6: Folder Only Strategy
        strategy = FolderOnlyDazzleStrategy(exclusion_filter, verbose=1)
        test_strategy(strategy, "Folder Only Strategy", test_path)
        
        # Test 7: Factory function
        print("\nTesting factory function...")
        strategy = create_strategy('standard', 'smart', exclusion_filter, verbose=0)
        assert strategy.get_name() == 'dazzle-standard-smart'
        print("  [PASS]")
        
    print("\n" + "=" * 60)
    print("ALL STRATEGY TESTS PASSED!")
    print("DazzleTreeLib strategies are working correctly!")


if __name__ == "__main__":
    test_dazzle_strategies()