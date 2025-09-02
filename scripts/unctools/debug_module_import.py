#!/usr/bin/env python3
"""Debug module-level import state."""

import sys

print("=" * 60)
print("MODULE IMPORT STATE DEBUG")  
print("=" * 60)

# First, test direct unctools import
print("1. Direct unctools import:")
try:
    import unctools
    print(f"   SUCCESS: {unctools.__file__}")
except Exception as e:
    print(f"   FAILED: {e}")

# Now test our module's import detection
print("\n2. Module-level variables in unc_handler:")
try:
    from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE, import_error
    print(f"   UNCTOOLS_AVAILABLE: {UNCTOOLS_AVAILABLE}")
    print(f"   import_error: {import_error}")
    
    # Let's see if we can check the actual import attempt
    print(f"   Module in sys.modules: {'unctools' in sys.modules}")
    if 'unctools' in sys.modules:
        print(f"   Cached unctools location: {sys.modules['unctools'].__file__}")
        
except Exception as e:
    print(f"   FAILED importing unc_handler: {e}")
    import traceback
    traceback.print_exc()

# Test creating handler without verbose first
print("\n3. Creating UNCHandler(verbose=False):")
try:
    from folder_datetime_fix.unc_handler import UNCHandler
    handler = UNCHandler(verbose=False)
    print(f"   SUCCESS: unctools_available = {handler.unctools_available}")
except Exception as e:
    print(f"   FAILED: {e}")

# Then with verbose
print("\n4. Creating UNCHandler(verbose=True):")
try:
    handler_v = UNCHandler(verbose=True)
    print(f"   (Output above shows what verbose prints)")
    print(f"   SUCCESS: unctools_available = {handler_v.unctools_available}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test import order - maybe there's an import order issue
print("\n5. Testing import sequence:")
print(f"   sys.modules keys containing 'unc': {[k for k in sys.modules.keys() if 'unc' in k.lower()]}")

# Check if there are multiple imports of our module
unc_modules = [k for k in sys.modules.keys() if 'unc_handler' in k or 'folder_datetime_fix' in k]
print(f"   folder_datetime_fix modules: {unc_modules}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)