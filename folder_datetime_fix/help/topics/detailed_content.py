"""
Detailed help content combining brief, standard, and detailed information.

This module integrates the simplified help from help_topics.py with the detailed
technical documentation from analyze_help.py and strategy_help.py.
"""

from ...help_lib import DetailedHelpContent

# Strategy help content with all detail levels
STRATEGY_DETAILED = DetailedHelpContent(
    id='strategy.overview',
    topic='strategy',
    brief='Choose how folders are scanned: shallow (fast), deep (accurate), or smart (adaptive)',
    standard="""TIMESTAMP CALCULATION STRATEGIES

The folder datetime fix tool supports three strategies for calculating
folder timestamps based on their contents:

1. SHALLOW (Fast but less accurate)
   - Only examines immediate children (files in the folder)
   - Ignores subdirectory contents
   - Fastest option for large directory trees
   - Best for: Quick scans, folders with few subfolders

2. DEEP (Slow but accurate)
   - Recursively examines ALL contents
   - Considers every file in every subfolder
   - Most accurate timestamp calculation
   - Best for: Final corrections, archival purposes

3. SMART (Adaptive - Default)
   - Automatically chooses between shallow and deep
   - Uses heuristics based on folder structure
   - Balances speed and accuracy
   - Best for: General use, mixed directory structures""",
    detailed="""TIMESTAMP CALCULATION STRATEGIES
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

Each processed folder uses the specified strategy independently.""",
    examples=[
        "fdtfix.py C:\\Photos --strategy shallow     # Quick photo folder scan",
        "fdtfix.py C:\\Projects --strategy deep      # Accurate project tree fix", 
        "fdtfix.py C:\\Documents --strategy smart    # Let tool decide (default)",
        "fdtfix.py C:\\Projects --depth 1 --strategy deep # Deep scan immediate subfolders"
    ],
    validation_tests=[
        "SHALLOW examines only immediate children",
        "DEEP recursively examines entire subtree",
        "SMART automatically chooses strategy"
    ],
    category='strategy',
    priority=10
)

# Analyze help content with all detail levels
ANALYZE_DETAILED = DetailedHelpContent(
    id='analyze.overview',
    topic='analyze',
    brief='Choose memory vs speed trade-offs: auto (adaptive), tree (fast), low-memory (safe)',
    standard="""ANALYSIS STRATEGIES

The --analyze parameter controls how folder-datetime-fix analyzes folder 
structures and computes timestamps. Different strategies offer trade-offs 
between memory usage, speed, and functionality.

AVAILABLE STRATEGIES:

1. AUTO (default) - Automatically selects the best strategy based on path characteristics
2. STANDARD - Streaming strategy with smart caching for repeated lookups  
3. LOW-MEMORY - Ultra-low memory mode for massive directory trees
4. TREE - Memory-efficient tree structure with bottom-up timestamp computation
5. FOLDER-ONLY - Ultra-minimal mode that only tracks folder structure""",
    detailed="""ANALYSIS STRATEGIES
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

MEMORY USAGE COMPARISON
=======================

Strategy     | Memory/10K folders | Speed    | Use Case
-------------|-------------------|----------|------------------
folder-only  | ~1MB              | Fastest  | Structure only
low-memory   | <1MB              | Slowest  | Massive trees
tree         | ~2MB              | Fast     | Deep hierarchies
standard     | ~3.5MB            | Fast     | General use
auto         | Varies            | Varies   | Automatic""",
    examples=[
        "fdtfix.py /path --analyze=auto        # Let tool decide (recommended)",
        "fdtfix.py //server/share --analyze=low-memory # For huge network shares",
        "fdtfix.py /path --analyze=tree --strategy=deep # Tree analysis with deep scan",
        "fdtfix.py /project --analyze=folder-only # Quick structure overview"
    ],
    validation_tests=[
        "AUTO calculates based on 1% RAM threshold",
        "TREE builds complete hierarchy",
        "LOW-MEMORY uses < 1MB regardless of size",
        "FOLDER-ONLY returns None timestamps"
    ],
    category='analyze',
    priority=20
)

# Registry of all detailed content
DETAILED_CONTENT_REGISTRY = {
    'strategy': STRATEGY_DETAILED,
    'analyze': ANALYZE_DETAILED,
}

def get_detailed_content(topic: str) -> DetailedHelpContent:
    """Get detailed content for a topic."""
    return DETAILED_CONTENT_REGISTRY.get(topic)

def get_all_topics() -> list:
    """Get list of all available detailed topics."""
    return list(DETAILED_CONTENT_REGISTRY.keys())