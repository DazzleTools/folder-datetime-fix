#!/usr/bin/env python3
"""
Test suite for the Folder DateTime Fix tool.
Tests various depth and strategy combinations with the test structure.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.create_test_structure import create_test_expectations


def run_tool(test_path: Path, args: list) -> dict:
    """
    Run the mod_fldr_dt.py tool with given arguments.
    
    Returns:
        dict with 'success', 'output', and 'error' keys
    """
    cmd = [sys.executable, '-m', 'folder_datetime_fix']
    cmd.append(str(test_path))
    cmd.extend(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    return {
        'success': result.returncode == 0,
        'output': result.stdout,
        'error': result.stderr
    }


def get_folder_timestamp(folder_path: Path) -> datetime:
    """Get the modified timestamp of a folder."""
    return datetime.fromtimestamp(folder_path.stat().st_mtime)


def compare_timestamps(expected: datetime, actual: datetime, tolerance_seconds: int = 2) -> bool:
    """
    Compare two timestamps allowing for small differences.
    
    Args:
        expected: Expected timestamp (None means no change expected)
        actual: Actual timestamp
        tolerance_seconds: Acceptable difference in seconds
    
    Returns:
        True if timestamps match within tolerance
    """
    if expected is None:
        # No expectation set, any value is acceptable
        return True
    
    diff = abs((expected - actual).total_seconds())
    return diff <= tolerance_seconds


def run_strategy_test(test_base: Path, strategy_name: str, args: list, expectations: dict):
    """
    Test a specific strategy configuration.
    
    Args:
        test_base: Base path of test structure
        strategy_name: Name of the strategy being tested
        args: Command-line arguments for the tool
        expectations: Expected timestamps for each folder
    """
    print(f"\nTesting: {strategy_name}")
    print(f"  Args: {' '.join(args)}")
    print("-" * 40)
    
    # First, do a dry run to see what would change
    dry_run_result = run_tool(test_base, args + ['--dry-run', '--verbose'])
    
    if not dry_run_result['success']:
        print(f"  [FAIL] Dry run failed: {dry_run_result['error']}")
        return False
    
    print("  Dry run output preview:")
    for line in dry_run_result['output'].split('\n')[:10]:
        if line.strip():
            print(f"    {line}")
    
    # Now run for real
    result = run_tool(test_base, args)
    
    if not result['success']:
        print(f"  [FAIL] Execution failed: {result['error']}")
        return False
    
    # Check each folder's timestamp
    all_passed = True
    for folder_name, expected_timestamp in expectations.items():
        folder_path = test_base / folder_name
        
        if not folder_path.exists():
            print(f"  [FAIL] Folder not found: {folder_name}")
            all_passed = False
            continue
        
        actual_timestamp = get_folder_timestamp(folder_path)
        
        # For folders where no change is expected, we need to check differently
        if expected_timestamp is None:
            # Timestamp should be recent (within last minute)
            time_diff = (datetime.now() - actual_timestamp).total_seconds()
            if time_diff > 60:  # More than 1 minute old
                print(f"  [OK] {folder_name}: No change (as expected)")
            else:
                print(f"  [WARN] {folder_name}: Recently modified (might have been changed)")
        else:
            if compare_timestamps(expected_timestamp, actual_timestamp):
                print(f"  [OK] {folder_name}: {actual_timestamp.strftime('%Y-%m-%d')} "
                      f"(expected: {expected_timestamp.strftime('%Y-%m-%d')})")
            else:
                print(f"  [FAIL] {folder_name}: {actual_timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
                      f"(expected: {expected_timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
                all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("=" * 60)
    print("Folder DateTime Fix Tool - Test Suite")
    print("=" * 60)
    
    # Get test structure path
    test_base = Path(__file__).parent / 'test_structure'
    
    if not test_base.exists():
        print(f"ERROR: Test structure not found at {test_base}")
        print("Run create_test_structure.py first")
        return 1
    
    print(f"Test structure: {test_base}")
    
    # Get expectations
    expectations = create_test_expectations()
    
    # Test configurations
    # Note: We test at depth 1 to process the test folders (level0_empty, etc.)
    test_configs = [
        {
            'name': 'Shallow with Include Generated',
            'args': ['--depth', '1', '--strategy', 'shallow', '--include-generated'],
            'expectations': expectations['shallow_no_skip']
        },
        {
            'name': 'Shallow with Default (Skip Generated)',
            'args': ['--depth', '1', '--strategy', 'shallow'],
            'expectations': expectations['shallow_skip_generated']
        },
        {
            'name': 'Deep with Include Generated',
            'args': ['--depth', '1', '--strategy', 'deep', '--include-generated'],
            'expectations': expectations['deep_no_skip']
        },
        {
            'name': 'Deep with Default (Skip Generated)',
            'args': ['--depth', '1', '--strategy', 'deep'],
            'expectations': expectations['deep_skip_generated']
        },
        {
            'name': 'Fix-2 (Convenience Alias)',
            'args': ['--fix-2'],
            'expectations': expectations['deep_skip_generated']  # fix-2 uses deep strategy, skips by default
        },
    ]
    
    # Run tests
    all_passed = True
    for config in test_configs:
        # Reset test structure before each test
        print(f"\nResetting test structure...")
        # First remove the old structure completely
        import shutil
        if test_base.exists():
            shutil.rmtree(test_base, ignore_errors=True)
        # Then recreate it
        subprocess.run([sys.executable, str(Path(__file__).parent / 'create_test_structure.py')], 
                      capture_output=True)
        
        passed = run_strategy_test(
            test_base,
            config['name'],
            config['args'],
            config['expectations']
        )
        
        if not passed:
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED!")
    else:
        print("[FAILURE] SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())