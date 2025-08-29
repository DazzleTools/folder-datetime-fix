# Analysis Strategies Guide

## Overview

The `--analyze` parameter controls how folder-datetime-fix analyzes folder structures and computes timestamps. Different strategies offer trade-offs between memory usage, speed, and functionality.

## Quick Reference

```bash
# Auto-select based on path characteristics (default)
folder-datetime-fix /path --fix-all

# Force specific strategy
folder-datetime-fix /path --fix-all --analyze=tree
folder-datetime-fix /path --fix-all --analyze=low-memory
folder-datetime-fix /path --fix-all --analyze=folder-only

# Combine with modifiers
folder-datetime-fix /path --fix-all --analyze=standard,no-cache
folder-datetime-fix /path --fix-all --analyze=auto=2.0  # Double threshold
```

## Available Strategies

### 1. `auto` (Default)
**Automatic strategy selection based on path characteristics**

- Samples folder structure to estimate size
- Detects network vs local paths
- Calculates memory threshold based on system RAM (1% target)
- Selects optimal strategy automatically

**When selected:**
- Small local paths → `standard` with caching
- Large local paths → `low-memory` without caching
- Network paths → Uses shallow scanning to reduce latency

**Threshold calculation:**
- 16GB RAM → ~470K folders threshold
- 32GB RAM → ~940K folders threshold
- 64GB RAM → ~1.9M folders threshold

**Customization:**
```bash
# Double the threshold (use more memory if needed)
--analyze=auto=2.0

# Half the threshold (more conservative)
--analyze=auto=0.5
```

### 2. `standard`
**Streaming strategy with smart caching**

- Processes folders as encountered
- Maintains cache for repeated lookups
- Supports shallow/deep/smart scanning modes
- Best for most use cases

**Memory usage:** ~350 bytes per cached folder

**Scan modes (via --strategy):**
- `shallow`: Only immediate files (fast, may miss nested updates)
- `deep`: All files recursively (accurate but slower)
- `smart`: Adaptive based on folder structure (default)

### 3. `low-memory`
**Ultra-low memory mode for massive trees**

- No caching (zero memory footprint for cache)
- Recomputes timestamps as needed
- Ideal for trees with millions of folders
- Slower but memory-safe

**Memory usage:** < 1MB regardless of tree size

**Use when:**
- Processing network shares with millions of folders
- System has limited available RAM
- One-time operations where speed isn't critical

### 4. `tree`
**Memory-efficient tree with bottom-up computation**

- Builds complete folder hierarchy in memory
- Computes timestamps bottom-up (children before parents)
- Each folder computed exactly once
- Optimal for deep hierarchies

**Memory usage:** ~200 bytes per folder

**Algorithm:**
1. Build tree structure (folders only)
2. Compute leaf folders first
3. Bubble up timestamps to parents
4. Extract results for requested depths

**Best for:**
- Deep folder hierarchies
- When parent folders depend on child timestamps
- Multiple operations on same tree structure

### 5. `folder-only`
**Ultra-minimal folder structure analysis**

- No file scanning at all
- Returns folder paths with `None` timestamps
- Minimal memory usage
- Fastest possible traversal

**Memory usage:** ~100 bytes per folder

**Use cases:**
- Quick folder structure analysis
- Preparing for other operations
- Memory-constrained environments
- When only folder paths are needed

## Strategy Selection Logic

```
┌─────────────────┐
│ User specifies  │──Yes──→ Use specified strategy
│   --analyze?    │
└────────┬────────┘
         │ No
         ↓
┌─────────────────┐
│  Path is UNC/   │──Yes──→ Consider network optimizations
│  Network share? │
└────────┬────────┘
         │ No
         ↓
┌─────────────────┐
│ Estimate folder │
│     count       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Count > system  │──Yes──→ Use low-memory strategy
│   threshold?    │
└────────┬────────┘
         │ No
         ↓
   Use standard
   with caching
```

## Memory Usage Comparison

| Strategy | Memory per 10K folders | Speed | Use Case |
|----------|------------------------|-------|----------|
| folder-only | ~1MB | Fastest | Structure only |
| low-memory | <1MB | Slowest | Massive trees |
| tree | ~2MB | Fast | Deep hierarchies |
| standard | ~3.5MB | Fast | General use |
| auto | Varies | Varies | Automatic |

## Performance Characteristics

### Network Shares
- Auto-strategy detects UNC paths
- Prefers `shallow` scanning to reduce round-trips
- Consider `--analyze=low-memory` for massive shares
- Network latency dominates over memory usage

### Local Drives
- Can use more aggressive caching
- `smart` scanning provides best accuracy
- Tree strategy excels with deep hierarchies
- Memory usage is primary concern

### System Files
- All strategies respect `--skip-generated`
- System folders filtered before processing
- No impact on strategy selection

## Advanced Usage

### Combining with Strategy Parameter

The `--analyze` parameter works with `--strategy`:

```bash
# Tree mode with deep scanning
folder-datetime-fix /path --analyze=tree --strategy=deep

# Low memory with shallow scanning
folder-datetime-fix /path --analyze=low-memory --strategy=shallow
```

### Force No Cache

Disable caching even in standard mode:

```bash
folder-datetime-fix /path --analyze=standard,no-cache
```

### Custom Memory Limits

Adjust auto-strategy thresholds:

```bash
# Use 2% of RAM instead of 1%
folder-datetime-fix /path --analyze=auto=2.0

# Conservative - use 0.5% of RAM
folder-datetime-fix /path --analyze=auto=0.5
```

## Troubleshooting

### Out of Memory Errors

If you encounter memory issues:

1. Use `--analyze=low-memory` to force minimal memory usage
2. Use `--analyze=folder-only` if timestamps aren't needed
3. Process smaller depth ranges separately
4. Increase system swap/pagefile

### Slow Performance

If analysis is too slow:

1. Use `--strategy=shallow` for faster scanning
2. Skip system files with `--skip-generated`
3. Limit depth with specific depth values
4. Consider `--analyze=tree` for deep hierarchies

### Incorrect Timestamps

If timestamps seem wrong:

1. Use `--strategy=deep` for complete accuracy
2. Check if system files are affecting results
3. Verify file permissions allow reading
4. Use `--verbose=2` to see what's being scanned

## Examples

```bash
# Analyze large network share
folder-datetime-fix \\server\share --fix-all --analyze=low-memory

# Local development folder with caching
folder-datetime-fix C:\projects --fix-all --analyze=standard

# Quick structure overview
folder-datetime-fix /path --depths=0,1,2 --analyze=folder-only

# Memory-constrained system
folder-datetime-fix /path --fix-all --analyze=auto=0.25

# Deep hierarchy optimization
folder-datetime-fix /path --fix-all --analyze=tree --strategy=smart
```

## See Also

- Run `folder-datetime-fix --help analyze` for quick reference
- Run `folder-datetime-fix --help strategy` for scanning strategies
- See [Performance Guide](performance.md) for optimization tips
- See [Memory Management](memory-management.md) for detailed analysis