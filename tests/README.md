# Testing Guide for Folder DateTime Fix Tool

This directory contains two types of tests for the folder datetime fix tool:

1. **Unit Tests** - For developers to verify individual components
2. **Integration Tests** - For testing the complete tool with realistic scenarios

## Unit Tests

Unit tests are designed for developers who want to understand and extend the codebase. They test individual components in isolation.

### Running Unit Tests

```bash
# Run all unit tests with summary
python tests/run_tests.py

# Run specific test module
python tests/test_folder_scanner.py
python tests/test_timestamp_fixer.py

# Run with verbose output
python -m unittest discover tests -v

# Run specific test class
python -m unittest tests.test_folder_scanner.TestFolderScanner

# Run specific test method
python -m unittest tests.test_folder_scanner.TestFolderScanner.test_deep_timestamp_calculation
```

### Unit Test Files

- **`test_folder_scanner.py`** (12 tests)
  - Depth-based folder traversal
  - Timestamp calculation strategies (shallow, deep, smart)
  - System file exclusion
  - Intermediate folder processing
  
- **`test_timestamp_fixer.py`** (12 tests)
  - Timestamp modification
  - Dry-run mode
  - Error handling
  - Report generation
  - Statistics tracking

- **`run_tests.py`**
  - Test runner that executes all unit tests
  - Provides summary and exit codes
  - Useful for CI/CD integration

### Writing New Unit Tests

To add new unit tests, create a new test file or add to existing ones:

```python
import unittest
from folder_scanner import FolderScanner

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        # Setup test environment
        pass
    
    def test_my_new_feature(self):
        # Test your feature
        scanner = FolderScanner()
        result = scanner.some_method()
        self.assertEqual(result, expected_value)
```

## Integration Tests

Integration tests verify the complete tool works correctly with realistic directory structures.

### Running Integration Tests

```bash
# Run the main integration test suite
python tests/test_mod_fldr_dt.py

# This will:
# 1. Create a realistic test directory structure
# 2. Run the tool with various configurations
# 3. Verify timestamps are correctly fixed
```

### Test Structure Generator

The integration tests use a generator to create consistent test structures:

```bash
# Create test structure manually for inspection
python tests/create_test_structure.py

# This creates:
# test_structure/
# ├── level0_empty/          (empty folder)
# ├── level0_only_system/    (only thumbs.db, desktop.ini)
# ├── level0_mixed/          (mix of user and system files)
# ├── level0_normal/         (typical user folders)
# └── level0_recent/         (demonstrates the core problem)
```

### Integration Test Scenarios

The integration tests verify these real-world scenarios:

1. **Empty folders** - No changes expected
2. **System-only folders** - Behavior with/without --skip-generated
3. **Mixed content** - System files corrupting folder dates
4. **Deep hierarchies** - 3-level folder structures
5. **Parent propagation** - Intermediate folders get updated

Each scenario is tested with:
- Different strategies (shallow, deep, smart)
- With and without --skip-generated flag
- Multiple depth configurations

## Test Coverage

### What's Tested

✅ **Core Functionality**
- Depth-based folder selection
- Timestamp calculation strategies
- System file detection and exclusion
- Parent folder propagation
- Dry-run mode
- Error handling

✅ **Edge Cases**
- Empty folders
- Folders with only system files
- Permission errors
- Non-existent paths
- Already-correct timestamps

✅ **Integration**
- Complete workflow from scan to fix
- Command-line argument parsing
- Multi-depth processing
- Report generation

### What's Not Yet Tested

⚠️ **Pending Coverage**
- UNC path handling (requires unctools)
- Network drive scenarios
- Very large directory trees (performance)
- Symbolic links and junctions
- Concurrent file modifications

## Performance Testing

For performance testing with large structures:

```python
# Create a large test structure
import os
from pathlib import Path
from datetime import datetime

def create_large_test(base_path, num_folders=1000, depth=5):
    """Create a large directory tree for performance testing."""
    for i in range(num_folders):
        path = Path(base_path)
        for d in range(depth):
            path = path / f"level{d}_folder{i}"
        path.mkdir(parents=True, exist_ok=True)
        
        # Add some files
        (path / "file.txt").write_text("content")
        
        # Add system file
        (path / "thumbs.db").write_text("system")

# Usage
create_large_test("./performance_test")
```

## Continuous Integration

For CI/CD pipelines:

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
    - name: Run tests
      run: |
        pip install -e .
        python tests/run_tests.py
```

The test runner returns:
- Exit code 0 if all tests pass
- Exit code 1 if any tests fail

## Debugging Test Failures

If tests fail, use these strategies:

1. **Run with verbose output**: Add `-v` flag
2. **Check test structure**: Manually inspect `test_structure/` folder
3. **Add print statements**: Tests use stdout for debugging
4. **Isolate the test**: Run single test method
5. **Check permissions**: Some tests require write access

## Test Maintenance

When modifying the codebase:

1. Run unit tests to verify components still work
2. Run integration tests to verify complete workflow
3. Add new tests for new features
4. Update tests when changing behavior
5. Document any new test scenarios

## Contributing Tests

When contributing new tests:

1. Follow existing naming conventions
2. Use descriptive test method names
3. Include docstrings explaining what's tested
4. Clean up test artifacts in tearDown()
5. Make tests independent (don't rely on order)

---

For questions about testing, see the main README.md or open an issue on GitHub.