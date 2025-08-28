import sys
print("Arguments received:")
for i, arg in enumerate(sys.argv):
    print(f"  [{i}]: {repr(arg)}")
    
if len(sys.argv) > 1:
    import os
    path = sys.argv[1]
    print(f"\nPath exists: {os.path.exists(path)}")
    
    try:
        import unctools
        print(f"Is UNC path: {unctools.is_unc_path(path)}")
        
        # Try to fix it
        if path.startswith('\\') and not path.startswith('\\\\'):
            fixed = '\\' + path
            print(f"Fixed path: {repr(fixed)}")
            print(f"Fixed exists: {os.path.exists(fixed)}")
    except ImportError:
        print("unctools not available")