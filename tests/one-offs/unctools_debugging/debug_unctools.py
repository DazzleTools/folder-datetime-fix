#!/usr/bin/env python3
"""Debug UNCtools import specifically in CLI context."""

import sys
print("=" * 60)
print("UNCtools Import Debug")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Working dir: {sys.path[0] if sys.path else 'None'}")
print()

# Test 1: Direct unctools import
print("1. Testing direct unctools import...")
try:
    import unctools
    print(f"   SUCCESS: {unctools.__file__}")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Test the exact import pattern from unc_handler.py
print("2. Testing unc_handler import pattern...")
try:
    # This mimics exactly what's in unc_handler.py lines 15-35
    import unctools
    from unctools import (
        convert_to_local,
        convert_to_unc, 
        normalize_path,
        is_unc_path,
        is_network_drive,
        is_subst_drive,
        get_path_type,
        get_network_mappings,
    )
    UNCTOOLS_AVAILABLE = True
    import_error = None
    print("   SUCCESS: All functions imported")
except ImportError as e:
    UNCTOOLS_AVAILABLE = False
    import_error = str(e)
    print(f"   ImportError: {e}")
except Exception as e:
    UNCTOOLS_AVAILABLE = False
    import_error = f"Unexpected error: {str(e)}"
    print(f"   Exception: {e}")

print(f"   UNCTOOLS_AVAILABLE: {UNCTOOLS_AVAILABLE}")
if import_error:
    print(f"   import_error: {import_error}")

print()

# Test 3: Test UNCHandler creation
print("3. Testing UNCHandler creation...")
try:
    from folder_datetime_fix.unc_handler import get_unc_handler
    handler = get_unc_handler(verbose=True)
    print(f"   Handler created, unctools_available: {handler.unctools_available}")
    if hasattr(handler, 'import_error') and handler.import_error:
        print(f"   Handler import_error: {handler.import_error}")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Debug complete")
print("=" * 60)