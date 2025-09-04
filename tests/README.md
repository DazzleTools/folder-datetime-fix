# Testing Guide for Modified DateTime Fix Tool

This directory contains the basic test coverage for the modified datetime fix tool, organized into regular tests and one-off tests.

## Test Structure

```
tests/
├── one-offs/                  # Historical and reference tests (excluded by default)
│   ├── test_issue15.py       # DazzleTreeLib Issue #15 reference test 1
│   ├── test_issue15_correct.py  # DazzleTreeLib Issue #15 reference test 2
│   └── test_issue15_simple.py   # DazzleTreeLib Issue #15 reference test 3
├── test_*.py                 # Regular test modules (run by default)
└── test_issue15_regression.py # Main regression test for DazzleTreeLib Issue #15
```

## Running Tests

### Using the Test Runner (Recommended)

The project includes `run_tests.py` in the root directory for easy test execution:

```bash
# Run fast tests only (default, excludes slow tests)
python run_tests.py

# Run ALL tests including slow ones
python run_tests.py --all

# Show information about slow tests
python run_tests.py --slow

# Run with less verbose output
python run_tests.py --quiet
```

### Using pytest Directly

```bash
# Run all tests except one-offs
python -m pytest tests/ --ignore=tests/one-offs

# Run specific test file
python -m pytest tests/test_folder_scanner.py

# Run with verbose output
python -m pytest tests/ -v

# Run only slow tests
python -m pytest tests/ -m slow

# Run tests excluding slow ones
python -m pytest tests/ -m "not slow"
```

## Test Categories

### Regular Tests (179 tests)

These tests run by default and verify core functionality:

- **`test_analysis_strategies.py`** (14 tests) - Analysis strategy selection and configuration
- **`test_cache_completeness.py`** (11 tests) - Cache completeness tracking
- **`test_cli_integration.py`** (20 tests) - Command-line interface testing
- **`test_dazzle_scanner.py`** (1 test) - DazzleTreeLib scanner integration
- **`test_dazzle_strategies.py`** (1 test) - DazzleTreeLib strategy patterns
- **`test_depth_ranges.py`** (14 tests) - Depth range processing
- **`test_early_termination.py`** (4 tests) - Early termination optimization
- **`test_exclusion_filter.py`** (22 tests) - File/folder exclusion patterns
- **`test_folder_scanner.py`** (17 tests) - Folder scanning and timestamp calculation
- **`test_folderonly_completeness.py`** (5 tests) - Folder-only completeness tracking
- **`test_issue15_regression.py`** (3 tests) - DazzleTreeLib Issue #15 regression tests
- **`test_max_depth_detection.py`** (8 tests) - Maximum depth detection
- **`test_permission_error_handling.py`** (10 tests) - Permission error handling
- **`test_timestamp_fixer.py`** (9 tests) - Timestamp fixing functionality
- **`test_tree_strategy.py`** (11 tests) - Tree traversal strategies
- **`test_unc_handler.py`** (18 tests) - UNC path handling
- **`test_unctools_integration.py`** (11 tests) - UNCTools integration

### Slow Tests

Tests marked with `@pytest.mark.slow` are excluded by default:

- **`test_issue15_regression.py::TestIssue15Regression::test_permission_errors_in_async_dont_crash`**
  - Tests permission errors in async context with Windows system directories
  - Can take several seconds depending on system configuration

### One-Off Tests

Located in `tests/one-offs/`, these are historical reference tests that document specific bug fixes:

- **DazzleTreeLib Issue #15 Tests** - Event loop crash bug fix verification
  - These tests document the evolution of the fix
  - Preserved for historical reference
  - Not run during normal test execution

## Test Coverage Areas

### ✅ Core Functionality
- Depth-based folder selection
- Timestamp calculation strategies (shallow, deep, smart)
- System file detection and exclusion
- Parent folder propagation
- Dry-run mode
- Error handling and recovery
- DazzleTreeLib integration

### ✅ Edge Cases
- Empty folders
- Folders with only system files
- Permission errors (async and sync)
- Non-existent paths
- Already-correct timestamps
- UNC paths and network drives
- Event loop error prevention (Issue #15)

### ✅ Integration
- Complete workflow from scan to fix
- Command-line argument parsing
- Multi-depth processing
- Report generation
- Cache utilization
- Strategy selection

## Writing New Tests

### Adding Regular Tests

Create new test files following the naming convention `test_*.py`:

```python
import unittest
from pathlib import Path

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("./test_temp")
        self.test_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_my_feature(self):
        """Test description."""
        # Test implementation
        self.assertEqual(actual, expected)
```

### Marking Slow Tests

If a test takes significant time, mark it as slow:

```python
import pytest

class TestSlowFeature(unittest.TestCase):
    @pytest.mark.slow
    def test_expensive_operation(self):
        """This test takes a long time."""
        # Expensive test implementation
```

### Adding One-Off Tests

One-off tests go in `tests/one-offs/` and are for documenting specific bug fixes:

```python
#!/usr/bin/env python
"""
One-off test for Issue #XX
==========================

Documents the fix for [specific issue description].
"""

# Test implementation focusing on the specific issue
```

## Integration Testing

For end-to-end testing of the complete tool:

```bash
# Run the main integration test
python tests/test_mod_fldr_dt.py

# Test with UNC paths (requires network access)
python fdtfix.py --unc-path "\\server\share" -fa -vv
```

## Performance Testing

To test with large directory structures:

```python
from tests.create_test_structure import create_large_test

# Create a performance test structure
create_large_test("./perf_test", num_folders=1000, depth=5)

# Run the tool and measure performance
python fdtfix.py ./perf_test --analyze
```

## Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-timeout pytest-asyncio
    - name: Run tests
      run: python run_tests.py
```

Exit codes:
- 0: All tests passed
- Non-zero: Test failures occurred

## Debugging Test Failures

When tests fail:

1. **Run with verbose output**: `python run_tests.py -v`
2. **Run specific test**: `python -m pytest tests/test_name.py::TestClass::test_method -v`
3. **Check test artifacts**: Inspect temporary directories created by tests
4. **Enable debug logging**: Set logging level in test files
5. **Check permissions**: Ensure write access to test directories

## Test Maintenance

When modifying code:

1. Run tests before making changes (baseline)
2. Make your changes
3. Run tests again to verify nothing broke
4. Add tests for new functionality
5. Update tests if behavior changes intentionally
6. Document any new test patterns

## Known Issues

- **Windows line endings**: Tests may show CRLF warnings on Windows
- **Permission tests**: Some tests require admin privileges on Windows
- **Slow tests**: Use `--all` flag to include slow tests in CI
- **Async warnings**: pytest-asyncio deprecation warnings are expected

---

For questions about testing, see the main README.md or open an issue on GitHub.