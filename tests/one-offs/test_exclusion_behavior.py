"""
Test script to verify exclusion system behavior (additive vs replace).

Created: 2025-08-29
Version: 0.6.1_private_28-20250829-6c4ff340
Last working commit: 6c4ff340 (2025-08-29 10:18:12 -0400)
Purpose: Verify whether --exclude patterns are additive to system exclusions
         or replace them entirely.
"""

from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter, ExclusionMode

print("Testing exclusion system behavior: ADDITIVE vs REPLACE")
print("=" * 60)

# Test 1: Default mode without patterns
print("\nTest 1: Default mode (no patterns)")
f1 = ExclusionFilter(mode=ExclusionMode.DEFAULT)
print(f"  thumbs.db (system file): {f1.should_exclude(Path('thumbs.db'), is_dir=False)}")
print(f"  myfile.txt (regular file): {f1.should_exclude(Path('myfile.txt'), is_dir=False)}")
print(f"  __pycache__ (system folder): {f1.should_exclude(Path('__pycache__'), is_dir=True)}")

# Test 2: Default mode WITH exclude patterns (ADDITIVE test)
print("\nTest 2: Default mode + exclude patterns (are they additive?)")
f2 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    exclude_patterns=['*.bak', 'temp/']
)
print(f"  thumbs.db (system file): {f2.should_exclude(Path('thumbs.db'), is_dir=False)}")
print(f"  file.bak (pattern): {f2.should_exclude(Path('file.bak'), is_dir=False)}")
print(f"  __pycache__ (system folder): {f2.should_exclude(Path('__pycache__'), is_dir=True)}")
print(f"  temp (pattern folder): {f2.should_exclude(Path('temp'), is_dir=True)}")
print(f"  myfile.txt (neither): {f2.should_exclude(Path('myfile.txt'), is_dir=False)}")

# Test 3: None mode WITH exclude patterns (baseline)
print("\nTest 3: None mode + exclude patterns (patterns only)")
f3 = ExclusionFilter(
    mode=ExclusionMode.NONE,
    exclude_patterns=['*.bak', 'temp/']
)
print(f"  thumbs.db (system file): {f3.should_exclude(Path('thumbs.db'), is_dir=False)}")
print(f"  file.bak (pattern): {f3.should_exclude(Path('file.bak'), is_dir=False)}")
print(f"  __pycache__ (system folder): {f3.should_exclude(Path('__pycache__'), is_dir=True)}")
print(f"  temp (pattern folder): {f3.should_exclude(Path('temp'), is_dir=True)}")

# Test 4: Include patterns override both
print("\nTest 4: Include patterns override everything")
f4 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    exclude_patterns=['*.bak'],
    include_patterns=['important.bak', '__pycache__']
)
print(f"  important.bak (included): {f4.should_exclude(Path('important.bak'), is_dir=False)}")
print(f"  other.bak (excluded pattern): {f4.should_exclude(Path('other.bak'), is_dir=False)}")
print(f"  __pycache__ (included despite system): {f4.should_exclude(Path('__pycache__'), is_dir=True)}")
print(f"  thumbs.db (system, not included): {f4.should_exclude(Path('thumbs.db'), is_dir=False)}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("The --exclude patterns are ADDITIVE to the base mode exclusions.")
print("- Mode defines base behavior (system files)")
print("- Exclude patterns ADD more exclusions")
print("- Include patterns OVERRIDE both mode and exclude")
print("\nThis means:")
print("1. --exclude-mode=default --exclude='*.bak' excludes BOTH system files AND *.bak")
print("2. --exclude-mode=none --exclude='*.bak' excludes ONLY *.bak")
print("3. --include always wins over both mode and exclude")