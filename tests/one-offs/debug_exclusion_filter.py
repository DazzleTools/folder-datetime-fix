"""
Debug script for ExclusionFilter pattern matching issues.

Created: 2025-08-29
Version: 0.6.0_private_28-20250829-6c4ff340
Last working commit: 6c4ff340 (2025-08-29 10:18:12 -0400)
Purpose: Debug why certain glob patterns were not matching correctly,
         specifically question mark patterns and directory markers.
"""

from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter
import fnmatch

# Test question mark pattern
print("TEST: Question mark pattern")
f = ExclusionFilter(exclude_patterns=['temp?.txt', '??.tmp'])
p = Path('a.tmp')

print('glob_excludes:', f.glob_excludes)
print('Pattern ??.tmp should match exactly 2 chars before .tmp')

# Manual pattern matching
path_str = str(p).replace('\\', '/')
name = p.name
print(f'\nTesting {name}:')
print(f'  fnmatch.fnmatch("{name}", "??.tmp"): {fnmatch.fnmatch(name, "??.tmp")}')
print(f'  fnmatch.fnmatch("{name.lower()}", "??.tmp"): {fnmatch.fnmatch(name.lower(), "??.tmp")}')

# What happens in _check_exclude_patterns
for pattern in f.glob_excludes:
    if '/' not in pattern:
        match = fnmatch.fnmatch(name.lower(), pattern.lower())
        print(f'  Pattern "{pattern}" vs "{name}": {match}')

# What actually happens
result = f.should_exclude(p, is_dir=False)
print(f'\nActual result: {result}')
print(f'Expected: False (1 char does not match ?? pattern)')