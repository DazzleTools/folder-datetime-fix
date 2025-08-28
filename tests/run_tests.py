#!/usr/bin/env python3
"""
Test runner for the Folder DateTime Fix tool.

This script runs all unit tests and provides a summary of results.
Can be used for continuous integration or local development.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Run all unit tests and return results."""
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Load all test modules
    test_modules = [
        'test_folder_scanner',
        'test_timestamp_fixer',
    ]
    
    # Create test suite
    suite = unittest.TestSuite()
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
            print(f"Loaded tests from {module}")
        except Exception as e:
            print(f"Warning: Could not load {module}: {e}")
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("Running Folder DateTime Fix Unit Tests")
    print("=" * 70)
    print()
    
    result = run_all_tests()
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())