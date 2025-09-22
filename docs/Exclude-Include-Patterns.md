# Exclude/Include Pattern Documentation

## Overview

The folder-datetime-fix tool provides powerful pattern-based filtering to control which files and directories are processed. This system uses a three-layer hierarchy:

1. **Base Mode** - Sets default exclusion behavior
2. **Exclude Patterns** - Adds additional exclusions (ADDITIVE to mode)
3. **Include Patterns** - Overrides both mode and exclude patterns

## Quick Start Examples

### Include a System Directory and Its Contents

**WRONG** - Directory excluded, traversal stops:
```bash
python -m folder_datetime_fix --include=".vscode/**"
# .vscode directory is excluded, so files inside are never checked!
```

**RIGHT** - Include directory for traversal:
```bash
python -m folder_datetime_fix --include=".vscode"
# .vscode directory is included, files follow default mode
```

**BEST** - Include directory AND contents:
```bash
python -m folder_datetime_fix --include=".vscode,.vscode/**"
# Both directory and all contents are explicitly included
```

**SELECTIVE** - Include directory but only specific files:
```bash
python -m folder_datetime_fix --include=".vscode,.vscode/*.json"
# Directory is traversed, but only .json files are included
```

## Exclusion Modes

### default (Default Mode)
Excludes common system and generated files/folders:
- System files: `thumbs.db`, `.DS_Store`, `desktop.ini`
- Version control: `.git/`, `.svn/`, `.hg/`
- Python: `__pycache__/`, `*.pyc`, `.pytest_cache/`
- Node.js: `node_modules/`, `package-lock.json`
- IDE: `.vscode/`, `.idea/`, `*.swp`
- Build: `dist/`, `build/`, `*.egg-info/`

### none
Includes everything by default (no automatic exclusions)

### files
Excludes only system FILES (not directories)

### folders  
Excludes only system FOLDERS (not files)

## Pattern Syntax

### Basic Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `*.txt` | All .txt files | `file.txt`, `doc.txt` |
| `test_*` | Items starting with test_ | `test_file.py`, `test_dir/` |
| `*_backup` | Items ending with _backup | `file_backup`, `dir_backup/` |
| `?.txt` | Single char + .txt | `a.txt`, `1.txt` |

### Advanced Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `**/*.py` | All .py files recursively | `src/main.py`, `tests/unit/test.py` |
| `**/test_*` | test_* files in any directory | `tests/test_file.py`, `src/test_util.py` |
| `src/**` | Everything under src/ | `src/file.py`, `src/utils/helper.py` |
| `*/` | All directories (with trailing slash) | `src/`, `tests/` (NOT `file.txt`) |

### Directory-Specific Patterns

**Important**: Patterns ending with `/` match ONLY directories:
```bash
# Exclude all directories named 'temp'
--exclude="temp/"

# Exclude all directories starting with 'test_'  
--exclude="test_*/"

# Include only the .git directory (not .gitignore file)
--include=".git/"
```

## Understanding Directory Traversal

**Critical Concept**: When a directory is excluded, traversal stops there. Files inside won't even be checked!

### Example: Processing .vscode Files

```bash
# Scenario: You want all .vscode configuration files

# WRONG - Won't work:
--include=".vscode/*.json"
# Why: .vscode directory is excluded by default mode, traversal stops

# CORRECT - Include directory first:
--include=".vscode,.vscode/*.json"
# Why: .vscode is included (allows traversal), then .json files are included

# ALSO CORRECT - Include everything:
--include=".vscode"
# Why: Directory and contents follow mode (usually includes .json files)
```

## The Three-Layer Hierarchy

### Layer 1: Base Mode
Sets the foundation for what's excluded:
```bash
# Default mode excludes system files
python -m folder_datetime_fix
# Excludes: .git/, __pycache__/, node_modules/, etc.

# None mode includes everything
python -m folder_datetime_fix --exclude-mode=none
# Excludes: nothing by default
```

### Layer 2: Exclude Patterns (ADDITIVE)
Adds MORE exclusions on top of the mode:
```bash
# Exclude .bak files IN ADDITION to system files
python -m folder_datetime_fix --exclude="*.bak"
# Excludes: system files (from mode) + *.bak files

# With none mode, only excludes what you specify
python -m folder_datetime_fix --exclude-mode=none --exclude="*.bak"
# Excludes: ONLY *.bak files
```

### Layer 3: Include Patterns (OVERRIDE)
Overrides BOTH mode and exclude patterns:
```bash
# Include .gitignore even though .git* is normally excluded
python -m folder_datetime_fix --include=".gitignore"

# Include important.bak even though *.bak is excluded
python -m folder_datetime_fix --exclude="*.bak" --include="important.bak"
```

## Common Use Cases

### Process Only Python Files
```bash
python -m folder_datetime_fix --exclude-mode=none --include="*.py,**/*.py"
```

### Exclude Test Directories
```bash
python -m folder_datetime_fix --exclude="test/,tests/,**/test_*/"
```

### Include Hidden Files (Unix)
```bash
python -m folder_datetime_fix --include=".*"
```

### Process Specific Project Folders
```bash
python -m folder_datetime_fix --include="src/,src/**,docs/,docs/**"
```

### Exclude Backup Files
```bash
python -m folder_datetime_fix --exclude="*.bak,*.backup,*~,*.tmp"
```

### Include node_modules for Analysis
```bash
python -m folder_datetime_fix --include="node_modules,node_modules/**"
```

## Backward Compatibility

The `--include-generated` (or `-ig`) flag still works and is equivalent to:
```bash
python -m folder_datetime_fix --exclude-mode=none
```

This includes all files, even system/generated ones.

## Pattern Matching Rules

1. **Patterns are case-sensitive** on Unix, case-insensitive on Windows
2. **Path separators**: Use forward slashes (/) even on Windows
3. **Multiple patterns**: Separate with commas
4. **Quoting**: Use quotes when patterns contain spaces or special characters
5. **Order doesn't matter**: All patterns are evaluated, includes always win

## Debugging Patterns

To understand why files are included/excluded:

1. **Test with small directories first**
2. **Use --exclude-mode=none** to isolate pattern behavior
3. **Add patterns incrementally** to see their effect
4. **Remember directory traversal** - parent must be included

### Debug Example
```bash
# See what's excluded by default
python -m folder_datetime_fix --dry-run

# Test your exclude pattern
python -m folder_datetime_fix --exclude-mode=none --exclude="your_pattern" --dry-run

# Test your include pattern  
python -m folder_datetime_fix --include="your_pattern" --dry-run
```

## Advanced Examples

### Complex Project Structure
```bash
# Include src and tests, but not test fixtures
python -m folder_datetime_fix \
  --include="src/,src/**,tests/,tests/**" \
  --exclude="tests/fixtures/,tests/fixtures/**"
```

### Documentation Files Only
```bash
# Process only markdown and rst files
python -m folder_datetime_fix \
  --exclude-mode=none \
  --include="*.md,**/*.md,*.rst,**/*.rst"
```

### Exclude Multiple Build Directories
```bash
# Exclude various build output directories
python -m folder_datetime_fix \
  --exclude="build/,dist/,target/,out/,*.egg-info/"
```

### Include Specific Hidden Directories
```bash
# Include .github and .vscode but not other hidden directories
python -m folder_datetime_fix \
  --include=".github/,.github/**,.vscode/,.vscode/**"
```

## Troubleshooting

### Files Not Being Included

**Problem**: Your include pattern matches files but they're not processed

**Solution**: Check if the parent directory is excluded
```bash
# Wrong:
--include="src/tests/*.py"  # If src/ is excluded, won't work

# Right:
--include="src/,src/tests/*.py"  # Include parent directory
```

### Too Many Files Excluded

**Problem**: More files excluded than expected

**Solution**: Check your exclusion mode
```bash
# Check what mode excludes
python -m folder_datetime_fix --exclude-mode=default --dry-run

# Use none mode for full control
python -m folder_datetime_fix --exclude-mode=none --exclude="only_what_you_want"
```

### Pattern Not Matching

**Problem**: Pattern doesn't match expected files

**Common Issues**:
1. Missing recursive marker: Use `**/*.txt` not `*.txt` for recursive
2. Wrong path separator: Use `/` not `\` even on Windows  
3. Case sensitivity: Check your platform's rules
4. Directory marker: Use `dir/` to match only directories

### Include Pattern Not Overriding

**Problem**: Include pattern doesn't override exclude

**Solution**: Check pattern syntax exactly matches path
```bash
# If file path is: ./src/test.bak
--exclude="*.bak" --include="src/test.bak"  # Correct
--exclude="*.bak" --include="test.bak"      # Wrong - paths don't match
```

## Best Practices

1. **Start simple**: Use modes when possible, add patterns as needed
2. **Test incrementally**: Add patterns one at a time
3. **Document patterns**: Comment complex pattern combinations
4. **Include parent directories**: For traversal to work
5. **Use specific patterns**: More specific is better than broad
6. **Consider maintenance**: Simple patterns are easier to understand

## Summary Quick Reference

```bash
# Include everything (no exclusions)
--exclude-mode=none

# Exclude additional patterns
--exclude="pattern1,pattern2"

# Include patterns (override everything)
--include="pattern1,pattern2"

# Legacy compatibility
--include-generated  # Same as --exclude-mode=none

# Common combinations
--include=".vscode,.vscode/**"            # Directory + contents
--exclude="*.bak" --include="keep.bak"    # Exclude with exception
--exclude-mode=none --include="*.py"      # Only Python files
```