"""
Test how --include patterns handle directories like .vscode.

Created: 2025-08-29
Version: 0.6.1_private_28-20250829-6c4ff340
Last working commit: 6c4ff340 (2025-08-29 10:18:12 -0400)
Purpose: Test if including a directory pattern like ".vscode" properly includes
         both the directory itself AND its contents.
"""

from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter, ExclusionMode

print("Testing how --include handles directories like .vscode")
print("=" * 60)

# Test 1: Default behavior (no include)
print("\nTest 1: Default mode - .vscode is excluded as system folder")
f1 = ExclusionFilter(mode=ExclusionMode.DEFAULT)
print(f"  .vscode (dir): {f1.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f1.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f1.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 2: Include just ".vscode" - does it include the directory?
print("\nTest 2: Include pattern '.vscode' (no slash)")
f2 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode']
)
print(f"  .vscode (dir): {f2.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f2.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f2.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 3: Include with trailing slash ".vscode/"
print("\nTest 3: Include pattern '.vscode/' (with slash)")
f3 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode/']
)
print(f"  .vscode (dir): {f3.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f3.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f3.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 4: Include with wildcard ".vscode/*"
print("\nTest 4: Include pattern '.vscode/*' (contents)")
f4 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode/*']
)
print(f"  .vscode (dir): {f4.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f4.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f4.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 5: Include both directory and contents
print("\nTest 5: Include patterns '.vscode' AND '.vscode/*'")
f5 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode', '.vscode/*']
)
print(f"  .vscode (dir): {f5.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f5.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f5.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 6: Include specific file only
print("\nTest 6: Include only '.vscode/settings.json'")
f6 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode/settings.json']
)
print(f"  .vscode (dir): {f6.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f6.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/tasks.json: {f6.should_exclude(Path('.vscode/tasks.json'), is_dir=False)}")

# Test 7: Include with recursive pattern
print("\nTest 7: Include pattern '.vscode/**' (recursive)")
f7 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode/**']
)
print(f"  .vscode (dir): {f7.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  .vscode/settings.json: {f7.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  .vscode/extensions/ext.json: {f7.should_exclude(Path('.vscode/extensions/ext.json'), is_dir=False)}")

print("\n" + "=" * 60)
print("OBSERVATIONS:")
print("1. Including '.vscode' (no slash) includes ONLY the directory itself")
print("2. Including '.vscode/' (with slash) includes ONLY the directory")
print("3. Including '.vscode/*' includes files IN the directory but NOT the directory")
print("4. Including '.vscode/**' includes everything under .vscode recursively")
print("\nIMPORTANT:")
print("For folder traversal to work, the DIRECTORY must not be excluded!")
print("If .vscode directory is excluded, we won't traverse into it to check files.")
print("\nRECOMMENDATION:")
print("To include a folder and its contents, use BOTH patterns:")
print("  --include='.vscode,.vscode/**'  (directory + all contents)")
print("OR just include the directory if you want everything:")
print("  --include='.vscode'  (allows traversal, mode controls files)")