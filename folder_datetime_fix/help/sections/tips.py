"""
Random tips pool for helpful hints.

Tips should be:
- Self-contained and actionable
- Not duplicate obvious content from basic examples
- Provide insights not immediately apparent
- Focus on best practices and lesser-known features
"""

# Pool of curated tips that provide additional value
TIPS_POOL = [
    # Basic tips
    "Use --dry-run first to preview changes safely before applying them",
    "The -f2 shortcut fixes a folder and its immediate children quickly",
    "Start with a small test folder before running on large directories",
    
    # Depth tips
    "Use --depth-to 3 instead of --depth 0 --depth 1 --depth 2 --depth 3",
    "Combine --depth-from and --depth-to to process specific depth ranges",
    "The --depth infinite option processes all depths (same as -fa)",
    
    # Strategy tips
    "Use --strategy shallow for folders with many direct files (like photos)",
    "Use --strategy deep for project folders with complex nested structures",
    "The --strategy smart option automatically chooses based on folder content",
    
    # Pattern tips
    "Use --exclude='*.bak' to skip backup files during processing",
    "Include patterns override both exclude patterns and mode settings",
    "Use --include='.git/' to process normally-excluded system folders",
    "Patterns support wildcards: * (any), ? (single), ** (recursive)",
    
    # Performance tips
    "Network shares work best with --strategy deep for accuracy",
    "Use -vv for detailed progress information on large operations",
    "The --max-depth option limits recursion to prevent deep traversal",
    "Use --analyze folder-only for fastest processing when appropriate",
    
    # Advanced tips
    "Combine --depth-to 3 with --strategy smart for balanced processing",
    "Use --exclude-mode=none --include='*.py' to process only Python files",
    "The --visualize option shows folder structure before processing",
    "Check docs/Recipes-and-Examples.md for common usage patterns",
    
    # Workflow tips
    "Always backup important data before running timestamp fixes",
    "Use --report to save a detailed log of all changes made",
    "The -vvv option enables trace-level debugging for troubleshooting",
    "Run without arguments to see quick help and usage examples",
    
    # Special tips
    "Use --help <topic> to learn about specific features in detail",
    "The --analyze option changes how timestamps are calculated",
    "System files like thumbs.db are skipped by default for safety",
    "Use --include-generated to process system files (rarely needed)",
]


def get_random_tip() -> str:
    """Get a random tip from the pool."""
    import random
    return random.choice(TIPS_POOL) if TIPS_POOL else ""


def get_tips() -> list:
    """Get all tips (for documentation purposes)."""
    return TIPS_POOL