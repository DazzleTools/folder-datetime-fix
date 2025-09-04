#!/usr/bin/env python3
"""
Test runner for modified-datetime-fix project.
Provides simple test execution with slow test management.

Usage:
    python run_tests.py           # Run fast tests only (default)
    python run_tests.py --all     # Run all tests including slow ones
    python run_tests.py --slow    # Show information about slow tests
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Slow tests that take significant time
SLOW_TESTS = [
    "tests/test_issue15_regression.py::TestIssue15Regression::test_permission_errors_in_async_dont_crash",
    # Add more slow tests here as they're identified
]


def run_tests(include_slow=False, verbose=True):
    """
    Run pytest with appropriate configuration.
    
    Args:
        include_slow: Whether to include slow tests
        verbose: Whether to show verbose output
    
    Returns:
        Exit code from pytest
    """
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--ignore=tests/one-offs",  # Always ignore one-offs directory
        "--tb=short",                # Short traceback format
        "--durations=10",            # Show 10 slowest tests
    ]
    
    if verbose:
        cmd.append("-v")
    
    if not include_slow:
        # Exclude slow tests
        cmd.extend(["-m", "not slow"])
    
    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


def show_slow_tests():
    """Display information about slow tests."""
    print("=" * 60)
    print("SLOW TEST INFORMATION")
    print("=" * 60)
    print()
    print(f"There are {len(SLOW_TESTS)} slow tests identified:")
    print()
    
    for test in SLOW_TESTS:
        print(f"  - {test}")
    
    print()
    print("These tests are excluded by default to keep the test suite fast.")
    print("Use '--all' to include them in the test run.")
    print()
    print("To run only slow tests:")
    print("  python -m pytest -m slow -v")
    print()
    print("To mark a test as slow, add the decorator:")
    print("  @pytest.mark.slow")
    print()


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for modified-datetime-fix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py           # Run fast tests only
  python run_tests.py --all     # Run all tests
  python run_tests.py --slow    # Show slow test info
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests including slow ones"
    )
    
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Show information about slow tests"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Less verbose output"
    )
    
    args = parser.parse_args()
    
    # Show slow test info if requested
    if args.slow:
        show_slow_tests()
        return 0
    
    # Run the tests
    print("=" * 60)
    print("MODIFIED-DATETIME-FIX TEST RUNNER")
    print("=" * 60)
    
    if args.all:
        print("Running ALL tests (including slow tests)...")
    else:
        print("Running fast tests only (excluding slow tests)...")
        print("Use --all to include slow tests")
    
    print()
    
    exit_code = run_tests(
        include_slow=args.all,
        verbose=not args.quiet
    )
    
    # Summary
    print()
    print("=" * 60)
    if exit_code == 0:
        print("SUCCESS: All tests passed!")
    else:
        print(f"FAILED: Tests failed with exit code {exit_code}")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())