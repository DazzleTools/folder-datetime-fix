# Setup Scripts

Environment setup and validation tools for folder-datetime-fix development.

## Quick Start Workflow

### 1️⃣ First Time Setup
```cmd
# Run the automated setup
setup_dev_environment.bat

# If successful, you're done!
# If not, continue to step 2
```

### 2️⃣ Validate Environment
```bash
# Check what's wrong
python validate_dev_environment.py

# Follow the specific fix recommendations shown
```

### 3️⃣ Manual Fixes (if needed)
```bash
# If UNCtools not found:
pip install unctools

# If import context issues:
set PYTHONPATH=C:\code\previous-unc-tests\UNC-protection\UNC-backup-test-dev-1;%PYTHONPATH%

# Re-run validation
python validate_dev_environment.py
```

## Scripts in This Directory

### `setup_dev_environment.bat` 
**Windows Automated Setup Script**

**What it does:**
- Checks Python availability
- Installs/updates UNCtools from PyPI or local editable
- Installs requirements.txt dependencies
- Sets PYTHONPATH if needed
- Runs validation automatically
- Provides clear success/failure status

**When to use:**
- **First time** setting up development environment
- **After** cloning the repository
- **After** Python version changes
- **When** UNCtools import issues occur

**Usage:**
```cmd
# From project root
scripts\setup\setup_dev_environment.bat

# Or from this directory
setup_dev_environment.bat
```

**Expected output on success:**
```
==================================================
SETUP COMPLETE
==================================================
Development environment is properly configured!
```

### `validate_dev_environment.py`
**Python Environment Validator**

**What it does:**
- Checks Python version (3.9+ required)
- Tests direct UNCtools import
- Tests UNCtools via our module
- Tests CLI execution context
- Checks environment variables
- Provides specific fix recommendations

**When to use:**
- **Before** starting development work
- **After** system/Python changes
- **When** troubleshooting import issues
- **To verify** setup was successful

**Usage:**
```bash
# From project root
python scripts/setup/validate_dev_environment.py

# Or from this directory
python validate_dev_environment.py
```

**Expected output on success:**
```
✓ Python version OK
✓ UNCtools found at: ...
✓ Module detects UNCtools as available
✓ CLI runs successfully
✓ CLI detects UNCtools

✅ All checks passed! Environment is properly configured.
```

## Common Issues & Solutions

### Issue 1: UNCtools Not Found
```
✗ Import failed: No module named 'unctools'
```

**Solution:**
```bash
pip install unctools
# OR for development
pip install -e C:\code\previous-unc-tests\UNC-protection\UNC-backup-test-dev-1
```

### Issue 2: Module Detection Failed
```
✗ Module detection failed: No module named 'unctools'
```

**Solution:**
```cmd
# Set PYTHONPATH for this session
set PYTHONPATH=C:\code\previous-unc-tests\UNC-protection\UNC-backup-test-dev-1;%PYTHONPATH%

# Or reinstall unctools
pip uninstall unctools
pip install unctools
```

### Issue 3: CLI Doesn't Detect UNCtools
```
✗ CLI doesn't detect UNCtools
This is the import context issue!
```

**Solution:**
```bash
# Run detailed diagnosis
python ../unctools/diagnose_unctools_env.py

# Use absolute Python path as workaround
C:\Python312\python.exe -m folder_datetime_fix [args]
```

## Environment Requirements

- **Python**: 3.9 or higher
- **pip**: Latest version recommended
- **UNCtools**: Required for enhanced UNC path support
- **Git**: Recommended for development

## Tips

1. **Run validation regularly** - Catches issues early
2. **Use setup script after cloning** - Ensures proper configuration
3. **Check validation before debugging** - Often reveals the issue
4. **Keep Python updated** - But re-validate after updates

## Related Tools

For deeper diagnosis of import issues, see:
- `../unctools/diagnose_unctools_env.py` - Comprehensive environment analysis
- `../unctools/debug_module_import.py` - Module import state debugging