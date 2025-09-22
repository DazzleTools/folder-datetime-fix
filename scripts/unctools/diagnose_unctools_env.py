#!/usr/bin/env python3
"""
Diagnostic script for UNCtools environment issues.

This script helps diagnose why UNCtools might not be detected in specific
environments like dazzle shell or custom CMD configurations.
"""

import sys
import os
import subprocess
from pathlib import Path

def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60)

def diagnose_python_environment():
    """Diagnose Python environment details."""
    print_separator("Python Environment")
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"Virtual environment: {sys.prefix}")
        print(f"Base Python: {getattr(sys, 'base_prefix', getattr(sys, 'real_prefix', 'Unknown'))}")
    else:
        print("Not in a virtual environment")

def diagnose_python_path():
    """Diagnose Python path and import locations."""
    print_separator("Python Path")
    
    print("sys.path entries:")
    for i, path in enumerate(sys.path):
        print(f"  {i:2d}: {path}")
    
    # Check for relevant environment variables
    env_vars = ['PYTHONPATH', 'PATH', 'PYTHONHOME']
    print("\nRelevant environment variables:")
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        if var == 'PATH':
            # Split PATH for readability
            print(f"  {var}:")
            if value != 'Not set':
                for path in value.split(os.pathsep):
                    if 'python' in path.lower() or 'pip' in path.lower():
                        print(f"    {path}")
            else:
                print(f"    {value}")
        else:
            print(f"  {var}: {value}")

def diagnose_unctools_import():
    """Diagnose UNCtools import specifically."""
    print_separator("UNCtools Import Test")
    
    # Test 1: Direct import
    print("1. Direct unctools import:")
    try:
        import unctools
        print(f"   SUCCESS: {unctools.__file__}")
        
        # List available functions
        functions = [attr for attr in dir(unctools) if not attr.startswith('_')]
        print(f"   Available functions: {functions}")
        
    except ImportError as e:
        print(f"   ImportError: {e}")
    except Exception as e:
        print(f"   Other error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check if it's in site-packages
    print("\n2. Site-packages check:")
    try:
        import site
        site_packages = site.getsitepackages()
        print(f"   Site-packages directories: {site_packages}")
        
        for site_dir in site_packages:
            unctools_path = Path(site_dir) / 'unctools'
            if unctools_path.exists():
                print(f"   Found unctools at: {unctools_path}")
            else:
                print(f"   No unctools in: {site_dir}")
                
    except Exception as e:
        print(f"   Error checking site-packages: {e}")
    
    # Test 3: pip show unctools
    print("\n3. Pip package info:")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'unctools'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   pip show unctools:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"   pip show failed: {result.stderr}")
    except Exception as e:
        print(f"   Error running pip show: {e}")

def diagnose_folder_datetime_fix_import():
    """Test import of our own package."""
    print_separator("Folder DateTime Fix Import")
    
    print("Testing folder_datetime_fix import:")
    try:
        # Try to import our package and check UNCtools detection
        from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE, import_error
        print(f"   Package imported successfully")
        print(f"   UNCTOOLS_AVAILABLE: {UNCTOOLS_AVAILABLE}")
        if import_error:
            print(f"   Import error: {import_error}")
        
        # Test UNCHandler creation
        from folder_datetime_fix.unc_handler import get_unc_handler
        handler = get_unc_handler(verbose=False)
        print(f"   UNCHandler created: unctools_available = {handler.unctools_available}")
        
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

def diagnose_cli_environment():
    """Test CLI in current environment."""
    print_separator("CLI Environment Test")
    
    print("Testing CLI --version:")
    try:
        result = subprocess.run([sys.executable, '-m', 'folder_datetime_fix', '--version'],
                              capture_output=True, text=True, timeout=30)
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"   Error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("   CLI --version timed out")
    except Exception as e:
        print(f"   Error running CLI: {e}")

def create_test_script():
    """Create a test script that mimics dazzle shell behavior.""" 
    print_separator("Test Script Creation")
    
    test_script = '''@echo off
echo Testing UNCtools detection in CMD environment
echo.

echo Python version:
python --version
echo.

echo Direct UNCtools test:
python -c "try: import unctools; print('SUCCESS: UNCtools available'); except Exception as e: print('FAILED:', e)"
echo.

echo UNC handler test:
python -c "from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE; print('UNC handler UNCTOOLS_AVAILABLE:', UNCTOOLS_AVAILABLE)"
echo.

echo CLI verbose test (should show UNCtools status):
python -m folder_datetime_fix --version
echo.

pause
'''
    
    script_path = Path("test_unctools_env.bat")
    script_path.write_text(test_script)
    
    print(f"Created test script: {script_path.absolute()}")
    print("Run this script in your dazzle shell environment to compare results:")
    print(f"   {script_path.absolute()}")

def main():
    """Run all diagnostics."""
    print("UNCtools Environment Diagnostic")
    print("Helps diagnose environment-specific import issues")
    
    diagnose_python_environment()
    diagnose_python_path()
    diagnose_unctools_import()
    diagnose_folder_datetime_fix_import()
    diagnose_cli_environment()
    create_test_script()
    
    print_separator("Diagnostic Complete")
    print("If UNCtools shows as available here but not in your dazzle shell,")
    print("compare the Python paths, environment variables, and executable paths.")

if __name__ == '__main__':
    main()