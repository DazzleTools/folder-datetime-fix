# Recipes and Examples - Folder DateTime Fix

This guide provides real-world examples and best practices for using the folder datetime fix tool. Always test with `--dry-run` first!

## Table of Contents
- [Quick Start](#quick-start)
- [Network Share Examples](#network-share-examples)
- [Local Folder Examples](#local-folder-examples)
- [Understanding Output](#understanding-output)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)

## Quick Start

### The Golden Rule: Always Dry-Run First!
Before making any changes, ALWAYS test with `--dry-run` to preview what will be modified:

```bash
# Preview changes without applying them (system files auto-skipped)
python mod_fldr_dt.py "C:\Projects" --depth 1 --dry-run
```

### Basic Workflow
1. **Preview** with --dry-run
2. **Review** the proposed changes
3. **Execute** without --dry-run when satisfied
4. **Verify** the results

## Network Share Examples

### Example: Fixing Project Folders on Network Share

This real example shows fixing folders corrupted by thumbs.db on a network share:

```bash
# Step 1: Preview what will change (DRY RUN)
python mod_fldr_dt.py --unc-path "\\server\projects\current-work" --fix-all --dry-run

# Expected output:
==================================================
Folder DateTime Fix Tool
==================================================
Target:        \\server\projects\current-work
Type:          UNC Network Path
Depths:        [0, 1]
Strategy:      deep
System Files:  SKIPPED (default)
Mode:          DRY RUN
==================================================

Scanning folders...
Found 42 folders to process

Previewing changes...
[DRY RUN] Would update: \\server\projects\current-work
  Current: 2024-12-15 09:30:00  ->  New: 2024-10-20 14:23:00
[DRY RUN] Would update: \\server\projects\current-work\design
  Current: 2024-12-15 09:30:15  ->  New: 2024-09-15 11:45:32
[DRY RUN] Would update: \\server\projects\current-work\code
  Current: 2024-12-15 09:30:16  ->  New: 2024-10-20 14:23:00
...

==================================================
SUMMARY
==================================================
Total folders scanned: 42
Folders changed:       38
Folders skipped:       0
Empty folders:         4
==================================================
```

### Step 2: Apply the Changes (ACTUAL RUN)
Once you've reviewed and are satisfied with the preview:

```bash
# Apply the changes for real
python mod_fldr_dt.py --unc-path "\\server\projects\current-work" --fix-all

# Output will be similar but show:
Mode:          EXECUTE
...
Applying changes...
Updated: \\server\projects\current-work
  Old: 2024-12-15 09:30:00  ->  New: 2024-10-20 14:23:00
Updated: \\server\projects\current-work\design
  Old: 2024-12-15 09:30:15  ->  New: 2024-09-15 11:45:32
```

### Alternative UNC Path Formats

```bash
# Method 1: Using --unc-path (recommended for copy-paste from Windows)
python mod_fldr_dt.py --unc-path "\\server\share\projects" --fix-all --skip-generated --dry-run

# Method 2: Using forward slashes (avoids escaping issues)
python mod_fldr_dt.py "//server/share/projects" --fix-all --skip-generated --dry-run

# Method 3: Mapped drive (if you have one)
python mod_fldr_dt.py "Z:\projects" --fix-all --skip-generated --dry-run
```

## Local Folder Examples

### Fix Your Documents Folder
```bash
# Step 1: Preview (see what system files are affecting timestamps)
python mod_fldr_dt.py "%USERPROFILE%\Documents" --depth 1 --dry-run -v

# Step 2: Apply fixes to immediate subfolders only
python mod_fldr_dt.py "%USERPROFILE%\Documents" --depth 1 
# Step 3: Verify the changes
dir "%USERPROFILE%\Documents" /OD
```

### Fix Deep Project Structure
```bash
# Fix a project and all its subfolders (max 5 levels deep)
python mod_fldr_dt.py "C:\code\my-project" --fix-all --max-depth 5 --skip-generated --dry-run

# If preview looks good, run for real
python mod_fldr_dt.py "C:\code\my-project" --fix-all --max-depth 5 ```

### Fix Only the Root Folder
```bash
# Sometimes you only want to fix the top-level folder
python mod_fldr_dt.py "C:\Projects" --depth 0 ```

## Understanding Output

### What the Numbers Mean

When you see:
```
Total folders scanned: 36
Folders changed:       35
Folders skipped:       0
Empty folders:         1
```

- **Total folders scanned**: All folders examined at specified depths
- **Folders changed**: Folders whose timestamps were corrected
- **Folders skipped**: Folders that couldn't be processed (permissions, etc.)
- **Empty folders**: Folders with no files to base timestamp on

### Timestamp Format

Timestamps show as: `YYYY-MM-DD HH:MM:SS`
- **Current/Old**: What Windows currently shows (corrupted by system files)
- **New**: The actual last modification time of user files

## Common Scenarios

### Scenario 1: Photo/Video Archive
Your photo folders show "modified today" because of thumbs.db:

```bash
# Fix all year folders to show when photos were actually added
python mod_fldr_dt.py "D:\Photos" --depth 1 --skip-generated --dry-run
python mod_fldr_dt.py "D:\Photos" --depth 1 ```

### Scenario 2: Development Projects
Project folders corrupted by .vs, node_modules cache, etc:

```bash
# Fix project folders but preserve system file timestamps for debugging
python mod_fldr_dt.py "C:\code" --depth 1 --strategy shallow --dry-run
python mod_fldr_dt.py "C:\code" --depth 1 --strategy shallow
```

### Scenario 3: Shared Team Drive
Fix corruption on network drive without affecting deep structure:

```bash
# Only fix the immediate team folders
python mod_fldr_dt.py --unc-path "\\fileserver\teams" --fix-immediate --skip-generated --dry-run
python mod_fldr_dt.py --unc-path "\\fileserver\teams" --fix-immediate ```

### Scenario 4: Complete Cleanup
Fix everything in a directory tree:

```bash
# Careful - this processes everything!
python mod_fldr_dt.py "C:\Work" --fix-all --skip-generated --report cleanup.txt --dry-run

# Review the report file, then run if satisfied
python mod_fldr_dt.py "C:\Work" --fix-all --skip-generated --report cleanup-applied.txt
```

## Troubleshooting

### "Path does not exist" Error
```bash
# Check if path is accessible
dir "\\server\share"

# If it works in dir but not in tool, try:
# 1. Map to drive letter first
net use Y: \\server\share
python mod_fldr_dt.py "Y:\" --fix-all 
# 2. Use forward slashes
python mod_fldr_dt.py "//server/share" --fix-all ```

### "Permission denied" Errors
```bash
# Run as Administrator (Windows)
# Right-click Command Prompt -> Run as Administrator

# Or check specific folder permissions
icacls "C:\path\to\folder"
```

### Nothing Changes
```bash
# Check if system files are newer than user files
python mod_fldr_dt.py "C:\folder" --depth 0 -v --dry-run

# Try without --skip-generated to see all files
python mod_fldr_dt.py "C:\folder" --depth 0 --dry-run
```

### Slower on Network Drives
Network operations are naturally slower. For large structures:

```bash
# Process in smaller chunks
python mod_fldr_dt.py --unc-path "\\server\share\part1" --fix-all python mod_fldr_dt.py --unc-path "\\server\share\part2" --fix-all ```

## Best Practices

### 1. Always Start with Dry-Run
```bash
# Good practice
python mod_fldr_dt.py [path] [options] --dry-run  # ALWAYS FIRST
python mod_fldr_dt.py [path] [options]             # After review
```

### 2. Use -v for Diagnostics (Multiple Verbosity Levels)
```bash
# Basic progress (shows folders being processed)
python mod_fldr_dt.py "C:\Projects" --depth 1 --dry-run -v

# Detailed folder info (shows each folder and changes)
python mod_fldr_dt.py "C:\Projects" --depth 1 --dry-run -vv

# Debug output (shows scanning strategy and folder discovery)
python mod_fldr_dt.py "C:\Projects" --depth 1 --dry-run -vvv

# Full trace (shows every function call with arguments)
python mod_fldr_dt.py "C:\Projects" --depth 1 --dry-run -vvvv
```

### 3. Save Reports for Large Operations
```bash
python mod_fldr_dt.py "D:\Archive" --fix-all --report "archive-fix-$(date +%Y%m%d).txt" --dry-run
```

### 4. Test on Small Subset First
```bash
# Test on one subfolder before processing entire tree
python mod_fldr_dt.py "C:\Projects\test-project" --fix-all --skip-generated --dry-run
```

### 5. Understand the Strategies
- **shallow**: Only looks at immediate children (fastest)
- **deep**: Examines entire subtree (most accurate)
- **smart**: Chooses based on folder structure

## Safety Notes

1. **This tool modifies folder timestamps** - always preview with --dry-run
2. **Cannot be undone** - timestamps aren't versioned
3. **May affect backup software** - some backup tools use folder timestamps
4. **Requires write permissions** - run as admin if needed

## Quick Reference Card

```bash
# Most common commands
mod_fldr_dt.py "C:\folder" --depth 1 --skip-generated --dry-run  # Preview subfolder fixes
mod_fldr_dt.py "C:\folder" --fix-all --skip-generated --dry-run   # Preview folder + subfolders
mod_fldr_dt.py --unc-path "\\server\share" --fix-all --skip-generated --dry-run  # Network share

# After reviewing dry-run output, remove --dry-run to apply changes
```

---
*Remember: When in doubt, use --dry-run!*