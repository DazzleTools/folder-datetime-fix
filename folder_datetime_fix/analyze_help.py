#!/usr/bin/env python3
"""
Detailed help information for analysis strategies.
"""

ANALYZE_HELP = """
ANALYSIS STRATEGIES
===================

The --analyze parameter controls how folder-datetime-fix analyzes folder 
structures and computes timestamps. Different strategies offer trade-offs 
between memory usage, speed, and functionality.

AVAILABLE STRATEGIES
====================

1. AUTO (default)
-----------------
Automatically selects the best strategy based on path characteristics.

How it works:
- Samples folder structure to estimate size
- Detects network vs local paths  
- Calculates memory threshold based on system RAM (1% target)
- Selects optimal strategy automatically

Threshold calculation:
- 16GB RAM -> ~470K folders threshold
- 32GB RAM -> ~940K folders threshold
- 64GB RAM -> ~1.9M folders threshold

Customization:
  --analyze=auto      Use default 1% RAM threshold
  --analyze=auto=2.0  Double threshold (use more memory)
  --analyze=auto=0.5  Half threshold (more conservative)

2. STANDARD
-----------
Streaming strategy with smart caching for repeated lookups.

Memory usage: ~350 bytes per cached folder

When to use:
- General purpose scanning
- Multiple operations on same folders
- Good balance of speed and memory

Features:
- Processes folders as encountered
- Maintains cache for repeated lookups
- Works with all scan strategies (shallow/deep/smart)

3. LOW-MEMORY  
-------------
Ultra-low memory mode for massive directory trees.

Memory usage: < 1MB regardless of tree size

When to use:
- Processing network shares with millions of folders
- System has limited available RAM
- One-time operations where speed isn't critical

Trade-offs:
- No caching (recomputes timestamps as needed)
- Slower but memory-safe
- Ideal for trees with millions of folders

4. TREE
-------
Memory-efficient tree structure with bottom-up timestamp computation.

Memory usage: ~200 bytes per folder

How it works:
1. Builds complete folder hierarchy in memory
2. Computes leaf folders first  
3. Bubbles up timestamps to parents
4. Each folder computed exactly once

Best for:
- Deep folder hierarchies
- When parent folders depend on child timestamps
- Multiple operations on same tree structure
- Optimal computation order

5. FOLDER-ONLY
--------------
Ultra-minimal mode that only tracks folder structure.

Memory usage: ~100 bytes per folder

Features:
- No file scanning at all
- Returns folder paths with None timestamps
- Fastest possible traversal
- Minimal memory footprint

Use cases:
- Quick folder structure analysis
- Preparing for other operations
- Memory-constrained environments
- When only folder paths are needed

ADVANCED OPTIONS
================

Combining Multiple Options
--------------------------
Use comma-separated values to combine options:

  --analyze=standard,no-cache    Standard mode without caching
  --analyze=low-memory,no-cache  Force no cache (redundant but allowed)

Adjusting Auto Thresholds
-------------------------
Control memory usage by adjusting the multiplier:

  --analyze=auto=2.0   Use 2% of RAM (double default)
  --analyze=auto=0.25  Use 0.25% of RAM (very conservative)

MEMORY USAGE COMPARISON
=======================

Strategy     | Memory/10K folders | Speed    | Use Case
-------------|-------------------|----------|------------------
folder-only  | ~1MB              | Fastest  | Structure only
low-memory   | <1MB              | Slowest  | Massive trees
tree         | ~2MB              | Fast     | Deep hierarchies
standard     | ~3.5MB            | Fast     | General use
auto         | Varies            | Varies   | Automatic

NETWORK vs LOCAL PATHS
=======================

Network Shares:
- Auto-strategy detects UNC paths (\\\\server\\share)
- Prefers shallow scanning to reduce network round-trips
- Consider --analyze=low-memory for massive network shares
- Network latency often dominates over memory usage

Local Drives:
- Can use more aggressive caching
- Smart scanning provides best accuracy
- Tree strategy excels with deep hierarchies
- Memory usage is primary concern

COMBINING WITH --strategy
=========================

The --analyze parameter works with --strategy for fine control:

  # Tree analysis with deep file scanning
  --analyze=tree --strategy=deep
  
  # Low memory with shallow scanning (fastest)
  --analyze=low-memory --strategy=shallow
  
  # Standard with smart scanning (balanced)
  --analyze=standard --strategy=smart

EXAMPLES
========

# Let the tool decide (recommended)
folder-datetime-fix /path --fix-all

# Force low memory for huge network share
folder-datetime-fix \\\\server\\share --fix-all --analyze=low-memory

# Quick folder structure overview
folder-datetime-fix /path --depths=0,1,2 --analyze=folder-only

# Deep hierarchy with bottom-up computation
folder-datetime-fix /project --fix-all --analyze=tree

# Conservative memory usage on limited system
folder-datetime-fix /path --fix-all --analyze=auto=0.25

TROUBLESHOOTING
===============

Out of Memory:
- Use --analyze=low-memory or --analyze=folder-only
- Process smaller depth ranges separately
- Increase system swap/pagefile

Slow Performance:
- Use --strategy=shallow for faster scanning
- Skip system files with --skip-generated (default)
- Limit depth with specific values
- Try --analyze=tree for deep hierarchies

Incorrect Timestamps:
- Use --strategy=deep for complete accuracy
- Check if system files affect results
- Verify file permissions
- Use --verbose=2 to see scanning details
"""

def print_analyze_help():
    """Print detailed analyze strategy help."""
    print(ANALYZE_HELP)

if __name__ == '__main__':
    print_analyze_help()