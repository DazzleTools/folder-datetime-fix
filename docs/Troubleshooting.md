# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Folder DateTime Fix tool.

## Table of Contents

- [Common Issues](#common-issues)
- [Verbose Mode & Debugging](#verbose-mode--debugging)
- [Permission Errors](#permission-errors)
- [Network Share Issues](#network-share-issues)
- [Performance Problems](#performance-problems)
- [Unexpected Results](#unexpected-results)
- [Quick Reference](#quick-reference)

## Common Issues

### Nothing Changes After Running

**Symptom**: Folders still show wrong dates after running the tool.

**Possible Causes**:
1. System files are actually newer than your content
2. Permission issues preventing updates
3. Wrong depth levels specified

**Solutions**:

```bash
# Check what's being detected with verbose mode
folder-datetime-fix . --fix-2 -vv

# Include normally-excluded system files to see their impact
folder-datetime-fix . --fix-2 --include-generated -vv --dry-run

# Check if you have permission to modify
folder-datetime-fix . --fix-2 --strict
```

## Verbose Mode & Debugging

The tool provides multiple verbosity levels to help diagnose issues:

### Verbosity Levels

| Level | Flag | Shows | Use When |
|-------|------|--------|----------|
| **Silent** | `-q` | Errors only | Automation/scripts |
| **Normal** | (default) | Basic progress + changes | Regular use |
| **Verbose** | `-v` | Folder counts + all changes | Want more details |
| **Very Verbose** | `-vv` | Scan details + timing | Debugging issues |
| **Debug** | `-vvv` | Tree structure + internals | Deep debugging |
| **Trace** | `-vvvv` | All operations + cache hits | Maximum detail |

### Using Verbose Mode Effectively

```bash
# See what's being processed
folder-datetime-fix . --fix-all -v

# Debug why timestamps aren't changing
folder-datetime-fix . --fix-2 -vv

# Full debug output with tree visualization
folder-datetime-fix . --depth 1 -vvv

# Trace all operations (very detailed)
folder-datetime-fix . --depth 0 -vvvv
```

### Understanding Verbose Output

#### Level 1 (-v): Basic Information
```
Scanning folders...
Found 42 folders to process
Processing depth 0: 1 folders
Processing depth 1: 12 folders
Updated: C:\Projects (2024-01-15 -> 2023-10-20)
```

#### Level 2 (-vv): Detailed Operations
```
Target path: C:\Projects (local)
Strategy: shallow (immediate children only)
Scanning with standard strategy...
  Memory estimate: 15 folders, ~5KB
  Using cache: enabled
Processing: C:\Projects
  Current: 2024-01-15 10:30:00
  Calculated: 2023-10-20 14:23:00 (from 15 files)
  Result: Will update
```

#### Level 3 (-vvv): Debug with Tree Structure
```
Tree structure:
C:\Projects
├── src (2023-10-20)
│   ├── main.py (2023-10-20)
│   └── utils.py (2023-09-15)
├── docs (2023-08-10)
└── tests (2023-10-01)

Cache stats: 15 entries, 3 hits, 12 misses
Memory usage: 5.2KB
```

## Permission Errors

### Windows Permission Issues

**Run as Administrator**:
```cmd
# Right-click Command Prompt -> Run as Administrator
folder-datetime-fix C:\Windows\Temp --fix-all
```

**Handle permission errors gracefully**:
```bash
# Default behavior: Continue running on errors (but shows warnings)
folder-datetime-fix . --fix-all

# Using --strict stops on first error
folder-datetime-fix . --fix-all --strict
```

### Network Share Permissions

```bash
# Test with dry-run first
folder-datetime-fix //server/share --fix-all --dry-run

# Use credentials if needed (map drive first)
net use Z: \\server\share /user:domain\username
folder-datetime-fix Z:\ --fix-all
```

## Network Share Issues

### Slow Performance on Network Drives

```bash
# Use shallow scanning for network paths
folder-datetime-fix //server/share --fix-all --strategy shallow

# Use low-memory mode for large shares (slower but should work for infinite depth)
folder-datetime-fix //server/share --fix-all --analyze low-memory

# Process in smaller chunks
folder-datetime-fix //server/share --depth-to 2  # Just 0,1,2
folder-datetime-fix //server/share --depth 3     # Then depth 3
```

### UNC Path Formatting Issues

```bash
# Method 1: Use --unc-path with quotes
folder-datetime-fix --unc-path "\\server\share" --fix-all

# Method 2: Use forward slashes
folder-datetime-fix //server/share --fix-all

# Method 3: Map to drive letter
net use Y: \\server\share
folder-datetime-fix Y:\ --fix-all
```

## Performance Problems

### Out of Memory

```bash
# Force low-memory mode
folder-datetime-fix . --fix-all --analyze low-memory

# Process fewer depths at once
folder-datetime-fix . --depth 0 --depth 1
folder-datetime-fix . --depth 2 --depth 3

# Reduce cache usage
folder-datetime-fix . --fix-all --analyze standard,no-cache
```

### Very Slow Processing

```bash
# Use shallow strategy (faster but less accurate)
folder-datetime-fix . --fix-all --strategy shallow

# Limit depth for testing
folder-datetime-fix . --depth-to 3 --dry-run
```

### Finding the Bottleneck

```bash
# Time the operation
time folder-datetime-fix . --fix-2 -vv

# Check what's being scanned
folder-datetime-fix . --fix-2 -vvv | grep "Processing"

# See cache effectiveness
folder-datetime-fix . --fix-2 -vvvv | grep "Cache"
```

## Unexpected Results

### Folders Show Wrong Dates

```bash
# Check what files are being considered
folder-datetime-fix . --depth 0 -vvv

# See if system files are newer
folder-datetime-fix . --depth 0 --include-generated -vv --dry-run

# Try deep strategy for accuracy
folder-datetime-fix . --fix-2 --strategy deep
```

### Some Folders Not Updated

```bash
# Check if they're being excluded
folder-datetime-fix . --fix-all -vv | grep "Skipping"

# Force inclusion of specific patterns
folder-datetime-fix . --fix-all --include ".git,.svn"

# Check for permission issues
folder-datetime-fix . --fix-all --strict
```

## Getting Help

### Built-in Help

```bash
# General help
folder-datetime-fix --help

# Help on specific topics
folder-datetime-fix --help strategy
folder-datetime-fix --help analyze
folder-datetime-fix --help patterns
```

### Diagnostic Information

When reporting issues, include:

```bash
# Version information
folder-datetime-fix --version

# System information
python --version
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"  # Windows
uname -a   # Linux/Mac

# Diagnostic run
folder-datetime-fix . --depth 0 -vvvv --dry-run > debug.log 2>&1
```

### Reporting Issues

When [reporting issues](https://github.com/djdarcy/folder-datetime-fix/issues), please include:

1. The exact command you ran
2. Your operating system and Python version
3. The verbose output (`-vv` or `-vvv`)
4. What you expected vs what happened
5. A small reproducible example if possible

## Advanced Debugging

### Testing Specific Scenarios

```bash
# Test on a single folder
folder-datetime-fix "C:\TestFolder" --depth 0 -vvv

# Test timestamp calculation without applying
folder-datetime-fix . --fix-2 --dry-run -vv

# Compare strategies
folder-datetime-fix . --depth 0 --strategy shallow -vv --dry-run
folder-datetime-fix . --depth 0 --strategy deep -vv --dry-run

# Test exclusion patterns
folder-datetime-fix . --fix-all --exclude "*.tmp,cache" -vv
```

### Understanding Analysis Strategies

```bash
# Force specific analysis mode
folder-datetime-fix . --fix-all --analyze tree -vv
folder-datetime-fix . --fix-all --analyze low-memory -vv

# Check memory usage
folder-datetime-fix . --fix-all --analyze auto -vvv | grep "Memory"
```

## Quick Reference

### Most Useful Debug Commands

```bash
# Why isn't my folder updating?
folder-datetime-fix "C:\Problem\Folder" --depth 0 -vvv

# What's taking so long?
folder-datetime-fix . --fix-all -vv --dry-run | head -50

# What files are affecting timestamps?
folder-datetime-fix . --depth 0 --strategy deep -vvv

# Is it a permission problem?
folder-datetime-fix . --fix-2 --strict

# Is it excluding too much?
folder-datetime-fix . --fix-2 --include-generated -vv --dry-run
```