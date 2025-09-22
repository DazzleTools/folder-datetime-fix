#!/usr/bin/env python3
"""
Test UNCtools detection in various contexts to reproduce the issue where
UNCtools shows as "not found" even when it's installed.
"""

import sys
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_direct_import():
    """Test direct UNCtools import."""
    print("=" * 60)
    print("TEST 1: Direct UNCtools Import")
    print("=" * 60)
    
    try:
        import unctools
        print("✅ SUCCESS: UNCtools imported directly")
        print(f"   Location: {unctools.__file__}")
        print(f"   Functions available: {[f for f in dir(unctools) if not f.startswith('_')]}")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def test_unc_handler_import():
    """Test UNC handler detection."""
    print("\n" + "=" * 60)
    print("TEST 2: UNC Handler Detection")
    print("=" * 60)
    
    try:
        from folder_datetime_fix.unc_handler import get_unc_handler
        handler = get_unc_handler(verbose=True)
        print(f"   UNCtools available: {handler.unctools_available}")
        if not handler.unctools_available and hasattr(handler, 'import_error'):
            print(f"   Import error: {handler.import_error}")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def test_cli_subprocess():
    """Test CLI via subprocess to match exact user experience."""
    print("\n" + "=" * 60)
    print("TEST 3: CLI Subprocess (User's Exact Command)")
    print("=" * 60)
    
    # Test the exact command the user provided
    cmd = [
        sys.executable, '-m', 'folder_datetime_fix',
        '--unc-path', '\\\\aktuldjr\\j\\maisie-proj-org',
        '-fa', '--dry-run', '-vv'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30  # Add timeout in case it hangs
        )
        
        # Look for UNCtools messages in the output
        output_lines = result.stdout.split('\n')
        stderr_lines = result.stderr.split('\n')
        
        unctools_messages = []
        for line in output_lines + stderr_lines:
            if 'unctools' in line.lower() or 'UNCtools' in line:
                unctools_messages.append(line.strip())
        
        if unctools_messages:
            print("UNCtools-related messages:")
            for msg in unctools_messages:
                if 'not found' in msg.lower():
                    print(f"❌ {msg}")
                else:
                    print(f"✅ {msg}")
        else:
            print("❓ No UNCtools messages found in output")
        
        print(f"\nReturn code: {result.returncode}")
        
        # Show first few lines of output for context
        print("\nFirst 10 lines of stdout:")
        for i, line in enumerate(output_lines[:10]):
            print(f"  {i+1}: {line}")
            
        if result.stderr.strip():
            print("\nStderr:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
    except Exception as e:
        print(f"❌ Failed to run command: {e}")


def test_import_in_different_contexts():
    """Test imports in different contexts that might affect detection."""
    print("\n" + "=" * 60) 
    print("TEST 4: Import Context Testing")
    print("=" * 60)
    
    # Test 1: Import in fresh subprocess
    print("Test 4a: Fresh subprocess import...")
    result = subprocess.run([
        sys.executable, '-c',
        'try:\n'
        '    import unctools\n'
        '    print("SUCCESS: UNCtools available in subprocess")\n'
        'except Exception as e:\n'
        '    print(f"FAILED: {e}")'
    ], capture_output=True, text=True)
    
    print(f"   {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"   stderr: {result.stderr.strip()}")
    
    # Test 2: Import through our module structure
    print("\nTest 4b: Import through module structure...")
    result = subprocess.run([
        sys.executable, '-c',
        'import sys; sys.path.insert(0, "C:/code/modified_datetime_fix/local");\n'
        'from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE, import_error;\n'
        'print(f"UNCTOOLS_AVAILABLE: {UNCTOOLS_AVAILABLE}");\n'
        'if not UNCTOOLS_AVAILABLE: print(f"Import error: {import_error}")'
    ], capture_output=True, text=True)
    
    print(f"   {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"   stderr: {result.stderr.strip()}")


def test_path_handling():
    """Test the actual UNC path handling to see where it fails."""
    print("\n" + "=" * 60)
    print("TEST 5: UNC Path Handling")  
    print("=" * 60)
    
    try:
        from folder_datetime_fix.unc_handler import get_unc_handler
        handler = get_unc_handler(verbose=True)
        
        test_path = "\\\\aktuldjr\\j\\maisie-proj-org"
        print(f"Testing path: {test_path}")
        
        # Test path conversion
        converted_path, is_network = handler.convert_for_processing(test_path)
        print(f"Converted path: {converted_path}")
        print(f"Is network: {is_network}")
        
        # Test path info
        info = handler.get_path_info(test_path)
        print(f"Path info: {info}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("UNCtools Detection Investigation")
    print("Looking for why 'UNCtools not found' appears when it should be available")
    print()
    
    test_direct_import()
    test_unc_handler_import() 
    test_cli_subprocess()
    test_import_in_different_contexts()
    test_path_handling()
    
    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)