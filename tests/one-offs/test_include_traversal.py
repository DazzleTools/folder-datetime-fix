"""
Test how directory traversal works with include patterns.

Created: 2025-08-29
Version: 0.6.1_private_28-20250829-6c4ff340
Last working commit: 6c4ff340 (2025-08-29 10:18:12 -0400)
Purpose: Understand the interaction between directory exclusion and traversal.
"""

from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter, ExclusionMode

print("Understanding directory traversal with include patterns")
print("=" * 60)

# Key insight: os.walk won't traverse into excluded directories!
print("\nKEY CONCEPT:")
print("When a DIRECTORY is excluded, os.walk won't traverse into it.")
print("So files inside won't even be checked.")
print()

# Test scenario: We want .vscode folder and all its contents
print("SCENARIO: Include .vscode and all its contents")
print("-" * 40)

print("\n1. BAD: Including only '.vscode/*' or '.vscode/**'")
f1 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode/**']
)
print(f"  .vscode (dir) excluded? {f1.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  -> Directory is EXCLUDED, so traversal STOPS here!")
print(f"  .vscode/settings.json excluded? {f1.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  -> File pattern matches, but we'd never get here in traversal")

print("\n2. GOOD: Including '.vscode' (allows traversal)")
f2 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode']
)
print(f"  .vscode (dir) excluded? {f2.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  -> Directory is INCLUDED, traversal continues!")
print(f"  .vscode/settings.json excluded? {f2.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  -> File has no include pattern, falls back to mode (not excluded if not system file)")

print("\n3. BETTER: Include directory AND contents")
f3 = ExclusionFilter(
    mode=ExclusionMode.DEFAULT,
    include_patterns=['.vscode', '.vscode/**']
)
print(f"  .vscode (dir) excluded? {f3.should_exclude(Path('.vscode'), is_dir=True)}")
print(f"  -> Directory is INCLUDED, traversal continues!")
print(f"  .vscode/settings.json excluded? {f3.should_exclude(Path('.vscode/settings.json'), is_dir=False)}")
print(f"  -> File matches include pattern, definitely included!")

print("\n" + "=" * 60)
print("PRACTICAL EXAMPLES:")
print()
print("1. Include .vscode folder for traversal (files follow mode):")
print("   --include='.vscode'")
print()
print("2. Include .vscode and ALL contents:")
print("   --include='.vscode,.vscode/**'")
print()
print("3. Include .vscode but only specific files:")
print("   --include='.vscode,.vscode/*.json'")
print()
print("4. Include only specific files (directory must be included!):")
print("   --include='.vscode,.vscode/settings.json'")
print()
print("RULE OF THUMB:")
print("Always include the parent directory in your patterns if you want")
print("to include files inside it!")