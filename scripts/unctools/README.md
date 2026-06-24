# UNCtools Diagnostic Scripts

Deep diagnostic tools for troubleshooting UNCtools import and integration issues.

## Quick Diagnosis Workflow

### 🔍 When You See: "UNCtools not found - using basic path handling"

Follow this diagnostic workflow:

### 1️⃣ Run Environment Diagnostic
```bash
python diagnose_unctools_env.py

# Creates detailed report of:
# - Python environment
# - Import paths
# - UNCtools availability
# - CLI execution context
```

### 2️⃣ Check Module Import State
```bash
python debug_module_import.py

# Shows:
# - Module-level import cache
# - UNCTOOLS_AVAILABLE value
# - Import context differences
```

### 3️⃣ Compare Results
If direct import works but module detection fails, you have the **import context issue**.

### 4️⃣ Apply Fix
```bash
# Go to setup directory and run
cd ../setup
python validate_dev_environment.py
# Follow the fix recommendations
```

## Scripts in This Directory

### `diagnose_unctools_env.py`
**Expansive Environment Diagnostic Tool**

**What it does:**
- Tests Python executable and version
- Shows complete Python path (`sys.path`)
- Tests direct UNCtools import
- Checks pip package installation
- Tests import through our module
- Tests CLI execution environment
- Creates test batch script for cross-environment testing
- Provides detailed diagnostic output

**When to use:**
- **First tool** when UNCtools issues occur
- Setting up new development environments
- Comparing environments (dev vs production)
- Debugging complex import failures

**Usage:**
```bash
# From project root
python scripts/unctools/diagnose_unctools_env.py

# From this directory
python diagnose_unctools_env.py
```

**Key sections of output:**
```
PYTHON ENVIRONMENT - Shows Python details
PYTHON PATH - Lists all import paths
UNCTOOLS IMPORT TEST - Direct import test
FOLDER DATETIME FIX IMPORT - Module import test
CLI ENVIRONMENT TEST - Full CLI test
```

**Also creates:** `test_unctools_env.bat` for testing in different shells

### `debug_module_import.py`
**Module-Level Import State Analyzer**

**What it does:**
- Tests direct unctools import
- Shows module-level `UNCTOOLS_AVAILABLE` value
- Shows cached import error (if any)
- Tests UNCHandler creation with/without verbose
- Lists all loaded modules containing 'unc'
- Reveals import order and caching issues

**When to use:**
- When direct import works but CLI fails
- Debugging module import caching
- Understanding import context differences
- Investigating why `UNCTOOLS_AVAILABLE = False`

**Usage:**
```bash
# From project root
python scripts/unctools/debug_module_import.py

# From this directory  
python debug_module_import.py
```

**Critical output to check:**
```
2. Module-level variables in unc_handler:
   UNCTOOLS_AVAILABLE: False  # ← This is the problem!
   import_error: No module named 'unctools'
```

If `UNCTOOLS_AVAILABLE` is False but direct import works, you have the **import context issue**.

## Understanding the Import Context Issue

### The Problem
Python's import system behaves differently in different contexts:

| Context | Command | Result |
|---------|---------|--------|
| Direct | `python -c "import unctools"` | ✅ Works |
| Script | `python script.py` → imports module | ❌ Fails |
| Module | `from folder_datetime_fix.unc_handler import ...` | ❌ Cached failure |

### Root Cause
1. **Editable packages** (`pip install -e`) use special import hooks
2. **Script execution** changes import context
3. **Module-level imports** cache the first result
4. **Different shells** may have different Python paths

### The Fix
1. **Proper installation**: `pip install unctools` (not just editable)
2. **PYTHONPATH**: Add unctools location to Python path
3. **Absolute Python**: Use `C:\Python312\python.exe` explicitly

## Diagnostic Output Interpretation

### ✅ Good Output
```
1. Direct unctools import:
   SUCCESS: C:\...\unctools\__init__.py
   
2. Module-level variables:
   UNCTOOLS_AVAILABLE: True
   
3. CLI detects UNCtools:
   UNCtools is available for enhanced network path support
```

### ❌ Problem Output
```
1. Direct unctools import:
   SUCCESS: C:\...\unctools\__init__.py  # Works here!
   
2. Module-level variables:
   UNCTOOLS_AVAILABLE: False  # But fails here!
   import_error: No module named 'unctools'
```

This indicates the **import context issue**.

## Quick Fixes

### Fix: Reinstall UNCtools from PyPI
```bash
pip uninstall unctools
pip install unctools
```

### Fix 3: Use Absolute Python Path
```cmd
C:\Python312\python.exe -m folder_datetime_fix [arguments]
```

## Advanced Debugging

### Check Import Paths
```python
import sys
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")
```

### Check Loaded Modules
```python
import sys
unc_modules = [k for k in sys.modules.keys() if 'unc' in k.lower()]
print(f"Loaded modules with 'unc': {unc_modules}")
```

### Force Reimport
```python
import importlib
import sys
if 'unctools' in sys.modules:
    importlib.reload(sys.modules['unctools'])
```

## Related Documentation & Tools

- **`TROUBLESHOOTING.md`** - Comprehensive troubleshooting guide with step-by-step workflows
- `../setup/validate_dev_environment.py` - Quick validation with fixes
- `../setup/setup_dev_environment.bat` - Automated setup
- `../../tests/test_unctools_integration.py` - Integration tests

## Historical Context

These tools were created on 2025-08-30 to solve a critical issue where UNCtools was installed but not detected in specific development environments (dazzle shell). The investigation revealed Python import context sensitivity with editable packages.

See full postmortem: `../../private/claude/2025_08_30__19_00_00__unctools_import_failure_postmortem.md`