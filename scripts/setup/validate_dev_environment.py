#!/usr/bin/env python3
"""
Development Environment Validator

Validates that the development environment is properly configured for
folder-datetime-fix, with special attention to UNCtools availability.

This script helps prevent the import context issues that can occur with
editable package installations in complex shell environments.
"""

import sys
import os
import subprocess
from pathlib import Path


def check_python_version():
    """Verify Python version is adequate."""
    print("Checking Python version...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 9):
        print("  [X] Python 3.9+ required")
        return False
    
    print("  [OK] Python version OK")
    return True


def check_unctools_direct():
    """Test direct UNCtools import."""
    print("\nChecking direct UNCtools import...")
    
    try:
        import unctools
        print(f"  [OK] UNCtools found at: {unctools.__file__}")
        
        # Check for key functions
        required_functions = ['is_unc_path', 'convert_to_local', 'convert_to_unc']
        missing = [f for f in required_functions if not hasattr(unctools, f)]
        
        if missing:
            print(f"  [X] Missing functions: {missing}")
            return False
            
        print(f"  [OK] All required functions available")
        return True
        
    except ImportError as e:
        print(f"  [X] Import failed: {e}")
        print("\n  To fix: pip install unctools")
        return False


def check_unctools_via_module():
    """Test UNCtools detection through our module."""
    print("\nChecking UNCtools via folder_datetime_fix module...")
    
    try:
        from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE, import_error
        
        if UNCTOOLS_AVAILABLE:
            print("  [OK] Module detects UNCtools as available")
            return True
        else:
            print(f"  [X] Module detection failed: {import_error}")
            print("\n  Possible fixes:")
            print("  1. Set PYTHONPATH to include unctools location")
            print("  2. Reinstall unctools: pip install --force-reinstall unctools")
            print("  3. Check for import context issues with: python scripts/diagnose_unctools_env.py")
            return False
            
    except Exception as e:
        print(f"  [X] Module import failed: {e}")
        return False


def check_cli_execution():
    """Test CLI can detect UNCtools."""
    print("\nChecking CLI execution context...")
    
    try:
        # Run CLI with version to test basic functionality
        result = subprocess.run(
            [sys.executable, '-m', 'folder_datetime_fix', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"  [X] CLI execution failed: {result.stderr}")
            return False
            
        print(f"  [OK] CLI runs successfully")
        
        # Test verbose mode to check UNCtools message
        result = subprocess.run(
            [sys.executable, '-m', 'folder_datetime_fix', '.', '--dry-run', '-v'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent  # Run from project root
        )
        
        if 'UNCtools is available' in result.stdout:
            print("  [OK] CLI detects UNCtools")
            return True
        elif 'UNCtools not found' in result.stdout:
            print("  [X] CLI doesn't detect UNCtools")
            print("\n  This is the import context issue!")
            print("  Run: python scripts/diagnose_unctools_env.py for detailed analysis")
            return False
        else:
            print("  ? UNCtools status unclear in CLI output")
            return None
            
    except subprocess.TimeoutExpired:
        print("  [X] CLI execution timed out")
        return False
    except Exception as e:
        print(f"  [X] CLI test failed: {e}")
        return False


def check_environment_variables():
    """Check relevant environment variables."""
    print("\nChecking environment variables...")
    
    pythonpath = os.environ.get('PYTHONPATH', '')
    if pythonpath:
        print(f"  PYTHONPATH is set:")
        for path in pythonpath.split(os.pathsep):
            print(f"    - {path}")
    else:
        print("  PYTHONPATH not set (using defaults)")
    
    # Check for development indicators
    if os.path.exists('.git'):
        print("  [OK] Git repository detected (development environment)")
    
    # Check for virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"  [OK] Virtual environment active: {sys.prefix}")
    else:
        print("  [i] Not in a virtual environment")
    
    return True


def suggest_fixes(results):
    """Provide targeted fix suggestions based on results."""
    print("\n" + "=" * 60)
    print("RECOMMENDED ACTIONS")
    print("=" * 60)
    
    if not results['direct_import']:
        print("\n1. Install UNCtools (optional -- enables enhanced UNC support):")
        print("   pip install unctools")

    elif not results['module_detection']:
        print("\n1. Reinstall UNCtools:")
        print("   pip uninstall unctools")
        print("   pip install unctools")
    
    elif results['cli_execution'] is False:
        print("\n1. Fix CLI execution context:")
        print("   This is the complex import context issue.")
        print("   Run for detailed diagnosis:")
        print("   python scripts/diagnose_unctools_env.py")
        print()
        print("   Quick fix: Use absolute Python path")
        print("   C:\\Python312\\python.exe -m folder_datetime_fix ...")
    
    if all(results.values()):
        print("\n[ALL OK] All checks passed! Environment is properly configured.")
    else:
        print("\n[!] Some checks failed. Follow the recommendations above.")


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("DEVELOPMENT ENVIRONMENT VALIDATOR")
    print("Folder DateTime Fix - UNCtools Integration")
    print("=" * 60)
    
    results = {
        'python_version': check_python_version(),
        'direct_import': check_unctools_direct(),
        'module_detection': check_unctools_via_module(),
        'cli_execution': check_cli_execution(),
        'environment': check_environment_variables()
    }
    
    suggest_fixes(results)
    
    # Return exit code based on results
    critical_checks = ['python_version', 'direct_import', 'module_detection']
    if all(results.get(check, False) for check in critical_checks):
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())