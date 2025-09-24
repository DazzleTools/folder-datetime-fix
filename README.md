# Folder DateTime Fix

[![Version](https://img.shields.io/github/v/release/djdarcy/folder-datetime-fix?sort=semver&color=blue)](https://github.com/djdarcy/folder-datetime-fix/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://github.com/djdarcy/folder-datetime-fix/actions/workflows/main.yml/badge.svg)](https://github.com/djdarcy/folder-datetime-fix/actions)
[![License](https://img.shields.io/badge/license-GPL--3.0-green)](https://github.com/djdarcy/folder-datetime-fix/blob/main/LICENSE)

Folder-Datetime-Fix restores accurate folder dates by removing common corruptions created by background features from Windows system files, like thumbs.db, and beyond.

[Quick Start](#quick-start) • [Installation](#installation) • [Documentation](docs/) • [Report Issue](https://github.com/djdarcy/folder-datetime-fix/issues)

## The Problem

Windows Explorer creates hidden files (`thumbs.db`, `desktop.ini`) that corrupt your folder timestamps:

| Before                                        | After Fix                                    |
| --------------------------------------------- | -------------------------------------------- |
| 📁 "2019 Projects" → Modified: **Today** ❌     | 📁 "2019 Projects" → Modified: **Dec 2019** ✅ |
| 📁 "Old Photos" → Modified: **Yesterday**❌     | 📁 "Old Photos" → Modified: **Jun 2018** ✅    |
| 📁 "Archived Work" → Modified: **Last week** ❌ | 📁 "Archived Work" → Modified: **Mar 2020** ✅ |

This breaks chronological sorting and makes it difficult to find your actual recent work.

## Quick Start

Fix your folders in 3 simple steps:

```bash
# 1. Install
pip install folder-datetime-fix

# 2. Preview changes (always do this first!)
cd \your\project\folder
folder-datetime-fix . --fix-all --dry-run

# 3. Apply the fix
folder-datetime-fix . --fix-all
```

That's it! Your folders now show their real modification dates. 

## Installation

### From PyPI (Recommended)

```bash
pip install folder-datetime-fix
```

### From Source

```bash
git clone https://github.com/djdarcy/folder-datetime-fix.git
cd folder-datetime-fix
pip install -e .
```

## Common Use Cases

### Fix Everything (Most Common)

Fix all folders recursively, skipping system files automatically:

```bash
# Fix entire C: drive (preview first)
folder-datetime-fix C:\ --fix-all --dry-run
folder-datetime-fix C:\ --fix-all

# Fix current directory and everything below
folder-datetime-fix . --fix-all
```

### Fix Specific Folder

Fix just one folder without affecting subfolders:

```bash
folder-datetime-fix "C:\Projects" --depth 0
```

### Fix Folder + Immediate Children

Fix a folder and its immediate subfolders (great for deep project directories especially on network shares):

```bash
# Using the convenient alias
folder-datetime-fix "C:\Projects" --fix-2

# Or explicitly
folder-datetime-fix "C:\Projects" --depth 0 --depth 1 --strategy deep
```

### Network Drives

Fix timestamps on network shares and UNC paths:

```bash
# UNC path (use quotes for backslashes)
folder-datetime-fix --unc-path "\\server\share\projects" --fix-all --dry-run

# Or use forward slashes
folder-datetime-fix //server/share/projects --fix-all
```

## How It Works

The tool recalculates folder timestamps based on the actual content, excluding system-generated files:

1. **Scans** your folder structure at specified depths
2. **Analyzes** the real content (your files) vs system files
3. **Calculates** what the folder date should be
4. **Updates** the folder timestamp to match the newest actual content

### System Files Automatically Skipped

By default, these system files are ignored when calculating dates:
- `thumbs.db`, `desktop.ini` (Windows)
- `.DS_Store` (macOS)
- `$RECYCLE.BIN`, `System Volume Information`
- Other [system-generated files](docs/Exclude-Include-Patterns.md)

## Understanding Depth Levels

Depth controls which folders get fixed:

```
C:\Projects\            <- depth 0 (the root)
├── ProjectA\           <- depth 1
│   ├── src\            <- depth 2
│   └── docs\           <- depth 2
└── ProjectB\           <- depth 1
    └── data\           <- depth 2
```

Common depth patterns:
- `--depth 0` - Just the target folder
- `--depth 1` - Just immediate subfolders
- `--fix-2` - Target + immediate children (depth 0 and 1)
- `--fix-all` - Everything recursively

## Command Line Options

### Important Options

| Option | Description |
|--------|-------------|
| `--fix-all`, `-fa` | Fix entire tree recursively (most common) |
| `--fix-2`, `-f2` | Fix folder + immediate children |
| `--dry-run`, `-n` | Preview changes without applying |
| `--verbose`, `-v` | Show progress details (use `-vv` for more) |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--depth N` | Process specific depth level |
| `--strategy {shallow,deep,smart}` | How to scan folders |
| `--exclude PATTERNS` | Skip specific patterns |
| `--include PATTERNS` | Include normally-skipped items |
| `--analyze {auto,tree,low-memory}` | Memory/performance tradeoffs |

See full options with `folder-datetime-fix --help`

## Examples

### Preview Everything First (Recommended Workflow)

```bash
# Always preview changes before applying
folder-datetime-fix "C:\Important" --fix-all --dry-run --verbose

# Review the output, then apply if it looks good
folder-datetime-fix "C:\Important" --fix-all --verbose
```

### Fix Photos Folder

```bash
# Quick scan - just looks at immediate files
folder-datetime-fix "C:\Photos" --fix-all --strategy shallow

# Or deep scan - checks all nested folders for accuracy
folder-datetime-fix "C:\Photos" --fix-all --strategy deep
```

### Fix Development Projects

```bash
# Fix all your git repositories
folder-datetime-fix "C:\Code" --fix-all --include ".git"

# Exclude build artifacts
folder-datetime-fix "C:\Projects" --fix-all --exclude "node_modules,*.cache,dist"
```

### Large Network Shares

```bash
# Use low-memory mode for millions of files
folder-datetime-fix //server/archive --fix-all --analyze low-memory --dry-run
```

## Troubleshooting

### Nothing seems to change?

System files might be newer than your content:
```bash
# Check what's happening with verbose mode
folder-datetime-fix . --fix-2 -vv
```

### Permission errors?

Run as Administrator or use `--strict` to stop on errors:
```bash
# Windows: Run as Administrator
# Or continue past errors (default behavior)
folder-datetime-fix C:\ --fix-all

# Or stop immediately on any error
folder-datetime-fix C:\ --fix-all --strict
```

### Need more details?

- See [Troubleshooting Guide](docs/troubleshooting.md) for verbose mode and debugging
- See [Analysis Strategies](docs/Analyze-Strategies.md) for performance tuning
- See [Recipes and Examples](docs/Recipes-and-Examples.md) for more scenarios


## Support

- [Report Issues](https://github.com/djdarcy/folder-datetime-fix/issues)
- [Discussions](https://github.com/djdarcy/folder-datetime-fix/discussions)

## Documentation

- [Full Documentation](docs/)
- [Analysis Strategies Guide](docs/Analyze-Strategies.md) - Memory and performance options
- [Architecture Overview](docs/Architecture-Overview.md) - How it works internally
- [Exclude/Include Patterns](docs/Exclude-Include-Patterns.md) - Fine-grained control
- [Recipes and Examples](docs/Recipes-and-Examples.md) - Real-world scenarios

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines. Please feel free to open issues or submit pull requests.

Like the project?

[!["Buy Me A Coffee"](https://camo.githubusercontent.com/0b448aabee402aaf7b3b256ae471e7dc66bcf174fad7d6bb52b27138b2364e47/68747470733a2f2f7777772e6275796d6561636f666665652e636f6d2f6173736574732f696d672f637573746f6d5f696d616765732f6f72616e67655f696d672e706e67)](https://www.buymeacoffee.com/djdarcy)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.