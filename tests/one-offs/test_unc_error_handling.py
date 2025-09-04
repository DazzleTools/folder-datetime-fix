#!/usr/bin/env python3
"""
Test script to verify error handling with UNC paths that have permission issues.

This tests the new PolicyDrivenErrorAdapter approach with real UNC paths
that contain inaccessible folders like "System Volume Information".
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from folder_datetime_fix.analysis_strategies_dazzle import StandardDazzleStrategy
from folder_datetime_fix.exclusion_filter import ExclusionFilter


async def test_unc_path_with_permissions():
    """Test UNC path traversal with permission errors."""
    # Test path that should have "System Volume Information"
    test_path = Path(r"\\aktuldjr\j")
    
    # Create exclusion filter (can be empty for this test)
    exclusion_filter = ExclusionFilter()
    
    print(f"Testing UNC path: {test_path}")
    print("-" * 60)
    
    # Test with strict=False (should skip permission errors)
    print("\n1. Testing with strict=False (should continue on errors):")
    strategy = StandardDazzleStrategy(
        scan_strategy='shallow',
        exclusion_filter=exclusion_filter,
        verbose=2,
        strict=False
    )
    
    try:
        # Process at depth 0 (root level folders)
        results = strategy.analyze(test_path, [0])
        print(f"\nFound {len(results)} folders at depth 0")
        
        # Show first few results
        for path, timestamp in results[:5]:
            print(f"  - {path.name}: {timestamp}")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more")
        
        # Get statistics including skipped folders
        stats = strategy.get_statistics()
        print(f"\nStatistics:")
        print(f"  - Folders processed: {stats['folders_processed']}")
        print(f"  - Permission denied: {stats['permission_denied']}")
        if stats['permission_denied'] > 0:
            print(f"  - Skipped paths:")
            for path in list(stats.get('skipped_paths', []))[:3]:
                print(f"    * {path}")
            if len(stats.get('skipped_paths', [])) > 3:
                print(f"    ... and {len(stats.get('skipped_paths', [])) - 3} more")
        
    except Exception as e:
        print(f"Error with strict=False: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # Test with strict=True (should fail on first permission error)
    print("\n2. Testing with strict=True (should fail on permission error):")
    strategy_strict = StandardDazzleStrategy(
        scan_strategy='shallow',
        exclusion_filter=exclusion_filter,
        verbose=1,
        strict=True
    )
    
    try:
        results_strict = strategy_strict.analyze(test_path, [0])
        print(f"\nFound {len(results_strict)} folders at depth 0")
        print("WARNING: Expected to fail but succeeded - no permission errors?")
    except PermissionError as e:
        print(f"\nExpected permission error occurred: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


async def test_local_path_with_mock_errors():
    """Test with a local path to verify error handling works."""
    test_path = Path("C:/code")
    
    from folder_datetime_fix.exclusion_filter import ExclusionMode
    exclusion_filter = ExclusionFilter(
        mode=ExclusionMode.DEFAULT,
        exclude_patterns=['node_modules', '.git', '__pycache__']
    )
    
    print(f"\n\nTesting local path: {test_path}")
    print("-" * 60)
    
    strategy = StandardDazzleStrategy(
        scan_strategy='shallow',
        exclusion_filter=exclusion_filter,
        verbose=1,
        strict=False
    )
    
    results = strategy.analyze(test_path, [1, 2])
    print(f"\nFound {len(results)} folders at depths 1-2")
    
    # Show some results
    for path, timestamp in results[:5]:
        print(f"  - {path.relative_to(test_path)}: {timestamp}")
    
    stats = strategy.get_statistics()
    print(f"\nStatistics:")
    print(f"  - Folders processed: {stats['folders_processed']}")
    print(f"  - Permission denied: {stats['permission_denied']}")


def main():
    """Main test runner."""
    print("=" * 60)
    print("Testing PolicyDrivenErrorAdapter with UNC Paths")
    print("=" * 60)
    
    # Check if UNC path is accessible
    unc_path = Path(r"\\aktuldjr\j")
    if not unc_path.exists():
        print(f"\nWARNING: UNC path {unc_path} not accessible")
        print("Will test with local path instead\n")
        asyncio.run(test_local_path_with_mock_errors())
    else:
        print(f"\nUNC path {unc_path} is accessible")
        asyncio.run(test_unc_path_with_permissions())
        
        # Also test local path
        asyncio.run(test_local_path_with_mock_errors())
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    main()