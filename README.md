# Folder DateTime Fix

[![Version](https://img.shields.io/github/v/release/djdarcy/folder-datetime-fix?sort=semver&color=blue)](https://github.com/djdarcy/folder-datetime-fix/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green)](https://github.com/djdarcy/folder-datetime-fix/blob/main/LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

**Fix folder timestamps corrupted by system files like thumbs.db on Windows**

A Python CLI tool that restores accurate folder modified timestamps based on actual user file modifications, solving the Windows issue where system-generated files corrupt folder modified date times and break chronological sorting.

## The Problem

When browsing folders in Windows Explorer, it often creates hidden system files like `thumbs.db` and `desktop.ini`. These types of generated files update the folder's modified timestamp, making folders appear recently changed even when they haven't been touched in potentially months. This default Windows behavior frustratingly breaks the ability to sort folders by actual modification date to find recent work.

**Before**: Project folder shows "Modified: Today" because of thumbs.db  
**After**: Project folder shows "Modified: Oct 2024" when you actually worked on it

## Features

- **Depth-based processing**: Fix folders at specific depth levels from a base path
- **Multiple strategies**: Choose shallow (immediate children), deep (entire subtree), or smart (automatic)
- **System file exclusion**: Automatically skips thumbs.db, desktop.ini, .DS_Store by default
- **UNC path support**: Works with network shares and mapped drives
- **Dry-run mode**: Preview changes before applying them
- **Detailed reporting**: Verbose output and change logs
- **Parent folder propagation**: Updates intermediate folders when fixing deep structures

## Installation

### From PyPI (Coming Soon)

```bash
pip install folder-datetime-fix
```

### From Source

```bash
# Clone the repository
git clone https://github.com/djdarcy/modified_datetime_fix.git
cd modified_datetime_fix

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Usage After Installation

```bash
# Run as installed command
folder-datetime-fix --help

# Or run as Python module
python -m folder_datetime_fix --help

# Legacy command (backward compatibility)
mod_fldr_dt --help
```

## Quick Start

### Fix a single folder
```bash
# Preview what would change first (ALWAYS recommended)
folder-datetime-fix C:\Projects --depth 0 --dry-run -v

# Apply the fix after reviewing
folder-datetime-fix C:\Projects --depth 0

# Include system files in timestamp calculation (not recommended)
folder-datetime-fix C:\Projects --depth 0 --include-generated
```

### Fix all subfolders
```bash
# Preview fixes for immediate subfolders
folder-datetime-fix C:\Projects --depth 1 --dry-run -v

# Fix with deep scanning (looks at entire subtree)
folder-datetime-fix C:\Projects --depth 1 --strategy deep
```

### Convenience shortcuts
```bash
# Preview fixes for folder and immediate children
folder-datetime-fix C:\Projects --fix-2 --dry-run -v

# Fix entire tree recursively (use with caution on large trees)
folder-datetime-fix C:\Projects --fix-all --dry-run -v

# Fix only immediate subfolders
folder-datetime-fix C:\Projects --fix-immediate
```

### Network paths
```bash
# UNC paths - preview with progress (recommended to start with --dry-run)
folder-datetime-fix //server/share/projects --fix-all --dry-run -v

# UNC paths - use --unc-path for easy copy-paste from Windows
folder-datetime-fix --unc-path "\\server\share\projects" --fix-all --dry-run -v

# Works with mapped drives
folder-datetime-fix Z:\team-projects --depth 1 -v

# Note: Single backslash paths like \server\share are ambiguous and will show a warning
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version information |
| `--depth N` | `-d N` | Process folders at depth N (can be specified multiple times) |
| `--strategy` | `-s` | Timestamp calculation strategy: shallow, deep, or smart |
| `--include-generated` | `-ig` | Include system-generated files (normally skipped) |
| `--dry-run` | `-n` | Preview changes without applying them |
| `--verbose` | `-v` | Increase verbosity (-v=basic, -vv=detailed, -vvv=debug, -vvvv=trace) |
| `--quiet` | `-q` | Suppress output except errors |
| `--report FILE` | `-r FILE` | Save detailed report to file |
| `--fix-2` | | Convenience: Fix folder and immediate children |
| `--fix-all` | | Convenience: Fix entire tree recursively |
| `--fix-immediate` | | Convenience: Fix immediate subfolders only |

## Understanding Depth Levels

```
C:\Projects\              <- depth 0
├── ProjectA\            <- depth 1
│   ├── src\            <- depth 2
│   └── docs\           <- depth 2
└── ProjectB\            <- depth 1
    └── data\           <- depth 2
```

- `--depth 0`: Fixes C:\Projects itself
- `--depth 1`: Fixes ProjectA and ProjectB
- `--depth 0 --depth 1`: Fixes all three folders at depths 0 and 1

## Understanding Strategies

- **shallow**: Sets folder timestamp based on immediate children only
- **deep**: Sets folder timestamp based on newest file in entire subtree
- **smart**: Automatically chooses based on folder structure

## System Files Handling

By default, system-generated files are automatically excluded from timestamp calculations. Use `--include-generated` if you need to include them.

System files automatically skipped:

- Windows: `thumbs.db`, `desktop.ini`, `IconCache.db`
- macOS: `.DS_Store`, `.localized`, `._*` files
- Cloud sync: `.dropbox`, `.dropbox.cache`
- IDEs: `.vscode/settings.json`, `.idea/`, `.vs/`
- Version control: `.git/index`, `.svn/entries`
- Package managers: `node_modules/.cache/`, `__pycache__/`

## Version Information

Check the current version with build metadata:

```bash
folder-datetime-fix --version
folder-datetime-fix -V
# Output: folder-datetime-fix 0.5.1_branch_build-20250828-commithash
```

The version format includes:
- Semantic version (MAJOR.MINOR.PATCH)
- Git branch name
- Build number (commit count)
- Date (YYYYMMDD)
- Short commit hash

## Verbose Mode

The tool provides progressive verbosity levels for debugging and monitoring:

- **`-v`** (basic): Shows folders being processed and basic progress
- **`-vv`** (detailed): Shows each folder's changes, skipped folders, and timestamps
- **`-vvv`** (debug): Shows scanning strategy, folder discovery at each depth, and progress counters
- **`-vvvv`** (trace): Shows complete function call trace with arguments and return values

Example usage:
```bash
# See basic progress
folder-datetime-fix C:\Projects --fix-2 --dry-run -v

# Debug why a folder isn't being fixed
folder-datetime-fix C:\Projects --depth 1 --dry-run -vvv

# Full trace for troubleshooting
folder-datetime-fix C:\Projects --depth 0 --dry-run -vvvv
```

## Examples

### Real-world scenario
```bash
# Your project folders are showing wrong dates because of thumbs.db
# This will fix all project folders to show actual last modification dates
folder-datetime-fix "C:\Users\YourName\Documents\Projects" --fix-2

# Check what would be fixed first (always recommended)
folder-datetime-fix "C:\Users\YourName\Documents\Projects" --fix-2 --dry-run -v
```

### Network share cleanup
```bash
# Fix team folders on network share, save report
folder-datetime-fix --unc-path "\\fileserver\team\projects" --depth 1 --strategy deep --report "fixes.txt"
```

### Recursive fix with max depth
```bash
# Fix everything up to 3 levels deep
folder-datetime-fix C:\Work --fix-all --max-depth 3
```

## Development

### Running Tests

```bash
# Run test suite
python tests/test_mod_fldr_dt.py

# Create test structure for manual testing
python tests/create_test_structure.py
```

### Project Structure

```
modified_datetime_fix/
├── folder_datetime_fix/      # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # Main CLI interface
│   ├── folder_scanner.py    # Directory traversal and timestamp logic
│   ├── timestamp_fixer.py   # Timestamp modification logic
│   ├── system_files.py      # System file detection patterns
│   ├── unc_handler.py       # UNC path handling
│   ├── trace_utils.py       # Debug tracing utilities
│   └── version.py           # Version information
├── tests/                   # Test suite
├── docs/                    # Additional documentation
├── scripts/                 # Utility scripts
└── setup.py                 # Package configuration
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines. Please feel free to open issues or submit pull requests.

Like the project?

[!["Buy Me A Coffee"](https://camo.githubusercontent.com/0b448aabee402aaf7b3b256ae471e7dc66bcf174fad7d6bb52b27138b2364e47/68747470733a2f2f7777772e6275796d6561636f666665652e636f6d2f6173736574732f696d672f637573746f6d5f696d616765732f6f72616e67655f696d672e706e67)](https://www.buymeacoffee.com/djdarcy)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Copyright (C) 2025 Dustin Darcy - [ScarcityHypothesis.org](https://ScarcityHypothesis.org)