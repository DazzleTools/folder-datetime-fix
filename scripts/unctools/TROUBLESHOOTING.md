# UNCtools Troubleshooting Guide

Comprehensive guide for diagnosing and fixing UNCtools import issues.

## Quick Troubleshooting Workflow

### Problem: "UNCtools not found - using basic path handling"

Follow this step-by-step process:

#### 1. First, run the validator:
```bash
python scripts/setup/validate_dev_environment.py
```

#### 2. If validation fails, run setup:
```cmd
scripts\setup\setup_dev_environment.bat
```

#### 3. For detailed diagnosis:
```bash
python scripts/unctools/diagnose_unctools_env.py
```

### Problem: Import works in Python but not in CLI

This is the import context issue. Run:
```bash
python scripts/unctools/debug_module_import.py
```

Then check if `UNCTOOLS_AVAILABLE` is False even though direct import works.

## Detailed Script Documentation

### `diagnose_unctools_env.py`
**Primary diagnostic tool for UNCtools import issues**

Comprehensive environment diagnostic that:
- Tests Python environment and paths
- Validates UNCtools installation and import
- Tests CLI functionality
- Creates cross-environment test scripts
- Generates detailed environment comparison data

**Usage:**
```bash
python scripts/unctools/diagnose_unctools_env.py
```

**Use When:**
- Setting up new development environments
- Troubleshooting "UNCtools not found" errors
- Verifying environment consistency across systems
- Debugging import path issues

### `debug_module_import.py`
**Module-level import state analysis**

Analyzes module import caching and state:
- Shows cached import results
- Reveals import context differences
- Tests module-level variable states
- Identifies import order issues

**Usage:**
```bash
python scripts/unctools/debug_module_import.py
```

**Use When:**
- Debugging cached import failures
- Investigating module loading order issues
- Understanding import context differences
- Troubleshooting package import problems

## The Import Context Issue - Deep Dive

### What Happens

Python's import system behaves differently in different execution contexts:

| Context | Command | Result |
|---------|---------|--------|
| Direct Python | `python -c "import unctools"` | ✅ Works |
| Script execution | `python script.py` | ❌ May fail |
| Module import | `from folder_datetime_fix.unc_handler import ...` | ❌ Cached failure |

### Root Cause

1. **Editable package installations** (`pip install -e`) use special import hooks
2. These hooks may not be available in all execution contexts
3. **Module-level imports** cache the first result (success or failure)
4. Once `UNCTOOLS_AVAILABLE = False` is cached, all subsequent uses fail

### The Fix

#### Reinstall UNCtools from PyPI
```bash
pip uninstall unctools
pip install unctools
```

#### Option 3: Use absolute Python path
```cmd
C:\Python312\python.exe -m folder_datetime_fix [arguments]
```

## Environment-Specific Issues

### Dazzle Shell Environment

The dazzle shell (`%COMSPEC% /E:ON /V:ON /k Z:\wintools\setenv.cmd`) can cause issues due to:
- Different PATH ordering
- Custom environment variables
- Different Python import contexts

**Solution:** Run `setup_dev_environment.bat` from within dazzle shell to configure for that environment.

### Virtual Environments

Virtual environments may have different import behaviors:
- Editable packages may not be visible
- Site-packages paths differ

**Solution:** Install UNCtools directly in the virtual environment:
```bash
pip install unctools
```

## Diagnostic Output Interpretation

### ✅ Healthy Output
```
1. Direct unctools import:
   SUCCESS: C:\...\unctools\__init__.py
   
2. Module-level variables in unc_handler:
   UNCTOOLS_AVAILABLE: True
   import_error: None
   
3. Creating UNCHandler(verbose=True):
   UNCtools is available for enhanced network path support
```

### ❌ Problem Output
```
1. Direct unctools import:
   SUCCESS: C:\...\unctools\__init__.py  # Works here!
   
2. Module-level variables in unc_handler:
   UNCTOOLS_AVAILABLE: False  # But fails here!
   import_error: No module named 'unctools'
```

This pattern indicates the **import context issue** - UNCtools can be imported directly but fails when imported through our module.

## Advanced Debugging Techniques

### Check Import Paths
```python
import sys
print("Python paths:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")
```

### Check Loaded Modules
```python
import sys
unc_modules = [k for k in sys.modules.keys() if 'unc' in k.lower()]
print(f"Modules with 'unc': {unc_modules}")
```

### Force Module Reload
```python
import importlib
import sys

# Clear cached import
if 'folder_datetime_fix.unc_handler' in sys.modules:
    del sys.modules['folder_datetime_fix.unc_handler']

# Try importing again
from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE
print(f"UNCTOOLS_AVAILABLE after reload: {UNCTOOLS_AVAILABLE}")
```

### Test Import in Different Contexts
```python
# Test 1: Direct import
import subprocess
result = subprocess.run([
    'python', '-c', 
    'import unctools; print("Direct import: OK")'
], capture_output=True, text=True)
print(result.stdout)

# Test 2: Through our module
result = subprocess.run([
    'python', '-c',
    'from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE; '
    'print(f"Module import: {UNCTOOLS_AVAILABLE}")'
], capture_output=True, text=True)
print(result.stdout)
```

## Historical Context

These scripts were created on 2025-08-30 to solve a critical UNCtools import issue that manifested only in specific development environments (dazzle shell). The investigation revealed Python import context sensitivity with editable package installations.

**Key Learning**: Editable package installations behave differently across execution contexts, leading to import failures that were cached at the module level.

**Resolution**: These diagnostic scripts help identify and resolve similar import context issues quickly.

## Related Documentation

- Full postmortem: `../../private/claude/2025_08_30__19_00_00__unctools_import_failure_postmortem.md`
- Design discussion: `../../private/claude/2025_08_30__19_15_00__unctools_import_design_discussion.md`
- Main README: `README.md` (in this directory)
- Setup tools: `../setup/README.md`