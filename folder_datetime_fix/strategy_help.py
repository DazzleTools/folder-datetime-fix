#!/usr/bin/env python3
"""
Detailed help information for folder datetime fix strategies.
"""

STRATEGY_HELP = """
TIMESTAMP CALCULATION STRATEGIES
=================================

The folder datetime fix tool supports three strategies for calculating 
folder timestamps based on their contents:

1. SHALLOW (default)
--------------------
Examines only the immediate children (files and folders) in each target folder.

When to use:
- Quick scans where you only care about direct modifications
- When subfolder timestamps are managed separately
- Performance-critical operations on large directory trees

How it works:
- Looks at files directly in the folder
- Looks at immediate subfolders' timestamps
- Does NOT examine files in subfolders

Example scenario:
  Photos/
    2024-vacation.jpg (June 15, 2024)
    2024-party.jpg    (July 20, 2024)
    thumbs.db         (Today - system file)
    Archive/          (May 1, 2024 - subfolder)
      old-pic.jpg     (Jan 1, 2020 - NOT examined)

Result (default behavior, system files skipped):
  Photos timestamp = July 20, 2024 (latest user file)

2. DEEP
-------
Recursively examines the entire subtree to find the newest file anywhere
within the folder hierarchy.

When to use:
- Complete timestamp correction based on all contents
- Project folders where work happens in subfolders
- When you want folders to reflect ANY activity within

How it works:
- Recursively scans all subfolders
- Finds the newest file in the entire tree
- Applies that timestamp to the target folder

Example scenario:
  Project/
    README.md         (March 1, 2024)
    src/
      main.py         (October 15, 2024 - newest in tree)
    docs/
      manual.pdf      (April 10, 2024)

Result (default behavior, system files skipped):
  Project timestamp = October 15, 2024 (newest file anywhere)

3. SMART
--------
Automatically chooses between shallow and deep based on folder structure
and contents.

When to use:
- Mixed directory structures
- When you're unsure which strategy is best
- Balanced approach between performance and accuracy

How it works:
- Analyzes folder structure
- Uses shallow for simple folders with mostly files
- Uses deep for complex project-like structures
- Considers factors like subfolder count and depth

Decision factors:
- Number of subfolders vs files
- Presence of project indicators (.git, src, etc.)
- Depth of folder structure

COMBINING WITH DEPTH LEVELS
===========================

Strategies work with depth levels to control which folders are processed:

  --depth 0                Process only the target folder
  --depth 1                Process immediate subfolders
  --depth 0 --depth 1      Process target AND immediate subfolders
  --depth infinite         Process all folders in the tree

Each processed folder uses the specified strategy independently.

Example:
  folder-datetime-fix C:\\Projects --depth 1 --strategy deep

This will:
1. Find all folders at depth 1 (immediate subfolders of Projects)
2. For EACH subfolder, scan its ENTIRE tree (deep strategy)
3. Update each subfolder's timestamp based on its tree

SYSTEM FILE HANDLING
====================

By default, system-generated files are automatically SKIPPED to show true
user modification dates. Use --include-generated to change this behavior.

Default behavior (system files skipped):
- System files like thumbs.db, desktop.ini are ignored
- Folders show actual last user modification date
- Empty folders (containing only system files) are skipped

With --include-generated flag:
- All files considered, including system files
- Folders may show today's date due to recent system file updates
- Empty folders with only system files will be processed

Common system files skipped by default:
- Windows: thumbs.db, desktop.ini, IconCache.db
- macOS: .DS_Store, .localized
- IDEs: .vscode/settings.json, .idea/
- Version control: .git/index
"""

def print_strategy_help():
    """Print detailed strategy help."""
    print(STRATEGY_HELP)

if __name__ == '__main__':
    print_strategy_help()