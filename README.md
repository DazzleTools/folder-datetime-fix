# Folder DateTime Fix

[![Python](https://img.shields.io/badge/python-%3E%3D3.7-darkgreen)](https://python.org/downloads)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/djdarcy/modified_datetime_fix/releases)

**Fix folder timestamps corrupted by system files like thumbs.db on Windows**

A Python CLI tool that restores accurate folder modified timestamps based on actual user file modifications, solving the Windows issue where system-generated files corrupt folder dates and break chronological sorting.

## The Problem

When you browse folders in Windows Explorer, it creates hidden system files like `thumbs.db` and `desktop.ini`. These files update the folder's modified timestamp, making folders appear recently changed when you haven't touched them in months. This breaks your ability to sort folders by actual modification date to find recent work.

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

### Direct Script Usage

```bash
# Run directly without installation
python mod_fldr_dt.py --help
```

## Quick Start

### Fix a single folder
```bash
# Fix a folder based on its immediate contents (system files auto-excluded)
mod_fldr_dt.py C:\Projects --depth 0

# Preview what would change without applying
mod_fldr_dt.py C:\Projects --depth 0 --dry-run

# Include system files in timestamp calculation (not recommended)
mod_fldr_dt.py C:\Projects --depth 0 --include-generated
```

### Fix all subfolders
```bash
# Fix all immediate subfolders (system files auto-excluded)
mod_fldr_dt.py C:\Projects --depth 1 --strategy shallow

# Fix with deep scanning (looks at entire subtree)
mod_fldr_dt.py C:\Projects --depth 1 --strategy deep
```

### Convenience shortcuts
```bash
# Fix folder and immediate children (alias for --depth 0 --depth 1 --strategy deep)
mod_fldr_dt.py C:\Projects --fix-2

# Fix entire tree recursively (alias for --depth infinite --strategy deep)
mod_fldr_dt.py C:\Projects --fix-all

# Fix only immediate subfolders
mod_fldr_dt.py C:\Projects --fix-immediate
```

### Network paths
```bash
# UNC paths - use forward slashes (recommended)
mod_fldr_dt.py //server/share/projects --fix-all

# UNC paths - use --unc-path for easy copy-paste from Windows
mod_fldr_dt.py --unc-path "\\server\share\projects" --fix-all

# Works with mapped drives
mod_fldr_dt.py Z:\team-projects --depth 1

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
mod_fldr_dt.py --version
mod_fldr_dt.py -V
# Output: mod_fldr_dt.py 0.5.1_branch_build-20250828-commithash
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
mod_fldr_dt.py C:\Projects --fix-2 --dry-run -v

# Debug why a folder isn't being fixed
mod_fldr_dt.py C:\Projects --depth 1 --dry-run -vvv

# Full trace for troubleshooting
mod_fldr_dt.py C:\Projects --depth 0 --dry-run -vvvv
```

## Examples

### Real-world scenario
```bash
# Your project folders are showing wrong dates because of thumbs.db
# This will fix all project folders to show actual last modification dates
mod_fldr_dt.py "C:\Users\YourName\Documents\Projects" --fix-2

# Check what would be fixed first (always recommended)
mod_fldr_dt.py "C:\Users\YourName\Documents\Projects" --fix-2 --dry-run -v
```

### Network share cleanup
```bash
# Fix team folders on network share, save report
mod_fldr_dt.py --unc-path "\\fileserver\team\projects" --depth 1 --strategy deep --report "fixes.txt"
```

### Recursive fix with max depth
```bash
# Fix everything up to 3 levels deep
mod_fldr_dt.py C:\Work --fix-all --max-depth 3
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
├── mod_fldr_dt.py           # Main CLI interface
├── folder_scanner.py        # Directory traversal and timestamp logic
├── timestamp_fixer.py       # Timestamp modification logic
├── system_files.py          # System file detection patterns
└── tests/
    ├── test_mod_fldr_dt.py  # Test suite
    └── create_test_structure.py  # Test data generator
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

Created by Dustin ([@djdarcy](https://github.com/djdarcy))

## Support

If you find this tool useful, consider supporting the project:

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/djdarcy)