"""
Debug script for recursive glob pattern (**) matching.

Created: 2025-08-29
Version: 0.6.0_private_28-20250829-6c4ff340
Last working commit: 6c4ff340 (2025-08-29 10:18:12 -0400)
Purpose: Debug why src/**/backup/* pattern was not matching correctly.
         Issue was with regex generation order - needed to handle ** before *.
"""

from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter

f = ExclusionFilter(exclude_patterns=['src/**/backup/*'])
test_path = Path('src/module/backup/file.txt')

print('Pattern: src/**/backup/*')
print('Test path:', test_path)
print('Should exclude:', f.should_exclude(test_path, is_dir=False))

# Check the regex
for pattern, regex in f.recursive_excludes:
    print(f'\nPattern {pattern} -> Regex: {regex.pattern}')
    path_str = str(test_path).replace('\\', '/')
    print(f'Path string: {path_str}')
    match = regex.search(path_str)
    print(f'Regex matches: {match}')
    if not match:
        print('Testing manual regex...')
        import re
        # What we expect
        expected_regex = r'^src/(.*/)backup/.*$'
        print(f'Expected regex: {expected_regex}')
        test_re = re.compile(expected_regex, re.IGNORECASE)
        print(f'Expected matches: {test_re.search(path_str)}')