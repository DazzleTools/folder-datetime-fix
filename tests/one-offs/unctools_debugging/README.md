# UNCtools Debugging Scripts

These scripts were created during the investigation of an UNCtools import failure issue that occurred in specific development environments (2025-08-30).

## Background

These debug scripts helped identify a Python import context issue where UNCtools was installed but not detected when running through certain execution contexts (specifically in dazzle shell environments).

## Scripts

### `debug_unctools.py`
Initial debug script to test UNCtools import in different contexts.

### `debug_verbose.py`
Tests verbose argument parsing to understand how CLI parameters affect UNCHandler creation.

### `debug_module_import.py`
**Most important script** - Reveals module-level import state and caching issues.
Shows the difference between direct imports and module context imports.

### `test_unctools_env.bat`
Windows batch script for testing UNCtools detection in CMD environment.
Created by diagnose_unctools_env.py for cross-environment testing.

## Key Finding

The issue was that Python's import system behaves differently when:
- Running direct Python commands: `python -c "import unctools"` ✅
- Running as a script: `python script.py` which imports our module ❌

This was due to editable package installation and import context differences.

## Status

**RESOLVED** - These scripts are kept for historical reference and in case similar issues arise.

For production-ready diagnostic tools, use:
- `scripts/diagnose_unctools_env.py` - Comprehensive environment diagnostic
- `scripts/validate_dev_environment.py` - Environment validation and auto-fix suggestions

See full postmortem: `private/claude/2025_08_30__19_00_00__unctools_import_failure_postmortem.md`