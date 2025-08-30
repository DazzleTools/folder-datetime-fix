"""
Help topic system for detailed documentation.

This module provides the topic help system, allowing users to get
detailed help on specific aspects of the tool.
"""

import textwrap
from typing import Dict, Callable


def print_with_padding(text: str, padding: str = " "):
    """
    Print text with left padding on each line.
    
    Args:
        text: The text to print
        padding: The padding to add (default: single space)
    """
    for line in text.split('\n'):
        print(padding + line if line else "")


def print_strategy_help():
    """Print detailed help about timestamp calculation strategies."""
    help_text = """TIMESTAMP CALCULATION STRATEGIES
=================================

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
   - Best for: General use, mixed directory structures

EXAMPLES:
  fdtfix.py C:\\Photos --strategy shallow     # Quick photo folder scan
  fdtfix.py C:\\Projects --strategy deep      # Accurate project tree fix
  fdtfix.py C:\\Documents --strategy smart    # Let tool decide (default)

INTERACTION WITH OTHER OPTIONS:
- The strategy applies at EACH depth level independently
- Works with --depth, --depth-to, and --depth-from options
- Can be overridden per-depth with --analyze options

See also: --help analyze, --help layers"""
    
    print_with_padding(help_text)


def print_analyze_help():
    """Print detailed help about analysis strategies."""
    help_text = """ANALYSIS STRATEGIES
===================

Analysis strategies control how the tool builds its internal representation
of the directory tree and calculates timestamps:

1. TREE (Full memory)
   - Builds complete tree structure in memory
   - Allows complex timestamp calculations
   - Best for: Small to medium directory trees
   - Memory usage: O(n) where n = total items

2. FOLDER-ONLY (Minimal memory)
   - Only tracks folder information
   - Ignores individual file details
   - Best for: Large trees, when file details don't matter
   - Memory usage: O(d) where d = directories only

3. LOW-MEMORY (Streaming)
   - Processes one branch at a time
   - Minimal memory footprint
   - Best for: Extremely large trees
   - Memory usage: O(depth)

4. AUTO (Adaptive - Default)
   - Automatically selects based on tree size
   - Monitors memory usage during scan
   - Switches strategies if needed
   - Best for: General use

ADVANCED OPTIONS:
You can combine strategies with modifiers:
  --analyze tree,ctime        # Use tree mode with creation times
  --analyze folder-only,fast  # Folder-only with speed optimizations

EXAMPLES:
  fdtfix.py C:\\Huge -fa --analyze low-memory   # Process huge tree
  fdtfix.py C:\\Small --analyze tree            # Full analysis for small tree
  fdtfix.py C:\\Work --analyze auto             # Let tool decide (default)

See also: --help strategy, --help layers"""
    
    print_with_padding(help_text)


def print_patterns_help():
    """Print detailed help about exclude/include patterns."""
    help_text = """EXCLUDE/INCLUDE PATTERNS GUIDE
===============================

Patterns use gitignore-style syntax for flexible file filtering:

BASIC PATTERNS:
  *.bak           Match all .bak files
  temp.txt        Match specific file name
  build/          Match directories named 'build' (trailing slash)
  
WILDCARDS:
  *               Any sequence of characters (except /)
  ?               Any single character
  [abc]           Any character in set
  [!abc]          Any character NOT in set

RECURSIVE PATTERNS:
  **/logs/        Match 'logs' directory at any depth
  docs/**         Match everything under 'docs'
  **/*.tmp        Match all .tmp files recursively
  
EXAMPLES:
  fdtfix.py . -fa --exclude="*.bak"            # Skip backup files
  fdtfix.py . -fa --exclude="temp/,cache/"     # Skip temp and cache dirs
  fdtfix.py . --exclude="**/node_modules/"     # Skip all node_modules
  fdtfix.py . --include=".git/"                # Include .git folders
  
PATTERN PRIORITY:
1. Base mode (--exclude-mode) applies first
2. Exclude patterns (--exclude) apply second
3. Include patterns (--include) override everything

TIPS:
- Use quotes around patterns to prevent shell expansion
- Comma-separate multiple patterns: --exclude="*.bak,*.tmp"
- Include patterns have highest priority
- Directory patterns should end with / for clarity

See also: --help layers"""
    
    print_with_padding(help_text)


def print_layers_help():
    """Print detailed help about how options layer together."""
    help_text = """HOW OPTIONS LAYER TOGETHER
===========================

Understanding how different options interact is key to using the tool effectively.

DEPTH OPTIONS:
  --depth N        Process ONLY specific depth level(s)
  --depth-to N     Process ALL depths from 0 to N (inclusive)
  --depth-from N   Start range at N (use with --depth-to)
  
  These determine WHICH folders are processed:
  - --depth 0 -> Only the root folder
  - --depth-to 3 -> Root and 3 levels down (depths 0,1,2,3)
  - --depth 2 --depth 4 -> Only depths 2 and 4

STRATEGY vs ANALYZE:
  --strategy       HOW to calculate timestamps (shallow/deep/smart)
  --analyze        HOW to build the tree structure (tree/folder-only/etc)
  
  These work at different levels:
  - Strategy: Applied at each folder when calculating its timestamp
  - Analyze: Applied once when scanning the entire tree

COMMON CONFUSION:
  Q: Why use --strategy deep with --depth infinite?
  A: --depth infinite means "process all depths"
     --strategy deep means "at each depth, scan recursively"
     Together: Process every folder, scanning each one fully

  Q: When should I use --analyze folder-only?
  A: When you have huge trees and only care about folder dates,
     not individual file details. Much faster and uses less memory.

EXAMPLE COMBINATIONS:
  # Fix everything, maximum accuracy:
  fdtfix.py . --depth-to inf --strategy deep --analyze tree
  
  # Quick fix of top 3 levels only:
  fdtfix.py . --depth-to 2 --strategy shallow --analyze folder-only
  
  # Fix specific depth with full accuracy:
  fdtfix.py . --depth 3 --strategy deep --analyze auto

CONVENIENCE SHORTCUTS:
  -fa -> --depth infinite --strategy deep
  -f2 -> --depth 0 --depth 1 --strategy deep
  -f1 -> --depth 1 --strategy shallow

See also: --help strategy, --help analyze"""
    
    print_with_padding(help_text)


# Registry of all help topics
HELP_TOPICS: Dict[str, Callable[[], None]] = {
    'strategy': print_strategy_help,
    'analyze': print_analyze_help,
    'patterns': print_patterns_help,
    'layers': print_layers_help,
}


def handle_help_topic(topic: str) -> bool:
    """
    Handle a help topic if it exists.
    
    Args:
        topic: The topic name to show help for
        
    Returns:
        True if topic was handled, False if not found
    """
    if topic in HELP_TOPICS:
        HELP_TOPICS[topic]()
        return True
    
    # Topic not found
    print(f" Unknown help topic: '{topic}'")
    print()
    print(" Available topics:")
    for topic_name in sorted(HELP_TOPICS.keys()):
        print(f"   - {topic_name}")
    return False


def get_available_topics() -> list[str]:
    """Get list of available help topics."""
    return sorted(HELP_TOPICS.keys())