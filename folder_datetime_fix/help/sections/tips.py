"""
Random tips pool for helpful hints with context awareness.

Tips should be:
- Self-contained and actionable
- Not duplicate obvious content from basic examples
- Provide insights not immediately apparent
- Focus on best practices and lesser-known features
"""

import random


def get_random_tip(exclude_sections=None) -> str:
    """Get a random tip, avoiding sections already displayed.
    
    Args:
        exclude_sections: List of section names already shown to avoid duplication
                         Can be: 'basic', 'strategy', 'advanced', 'network', 'quick_start'
        
    Returns:
        A formatted tip string with "TIP: " prefix, or empty string if no tips available
    """
    if exclude_sections is None:
        exclude_sections = []
    
    # Build available tips based on what's not already shown
    available_tips = []
    
    # Always-available general tips
    general_tips = [
        "Always use --dry-run first to preview changes safely",
        "Use -vv for detailed progress on large operations",
        "The . (dot) means current directory without typing the full path",
        "Use --report to generate a CSV log of all changes made",
        "Ctrl+C safely cancels operations without corrupting timestamps",
        "Always backup important data before running timestamp fixes",
        "Run without arguments to see quick help and usage examples",
    ]
    available_tips.extend(general_tips)
    
    # Section-specific tips (only add if section not shown)
    if 'basic' not in exclude_sections:
        available_tips.extend([
            "The -f2 shortcut means fix folder + immediate children",
            "Use --depth-to 3 instead of multiple --depth arguments",
            "Folder timestamps reflect the newest item inside",
            "Combine multiple --depth values to skip intermediate levels",
            "The --depth infinite option processes all depths (same as -fa)",
        ])
    
    if 'strategy' not in exclude_sections:
        available_tips.extend([
            "The 'smart' strategy auto-chooses based on folder structure",
            "Use 'deep' strategy for network shares to reduce queries",
            "Strategy affects accuracy: shallow=fast/approximate, deep=slow/precise",
            "Use --strategy shallow for folders with many direct files (like photos)",
            "The strategy applies at each depth level independently",
        ])
    
    if 'network' not in exclude_sections and 'quick_start' not in exclude_sections:
        available_tips.extend([
            "Forward slashes (//server/share) work as UNC alternatives",
            "Mapped drives can be faster than UNC paths due to caching",
            "The --unc-path option handles Windows path escaping automatically",
            "Network shares work best with --strategy deep for accuracy",
            "High latency networks benefit from --strategy deep to minimize queries",
        ])
    
    if 'advanced' not in exclude_sections:
        available_tips.extend([
            "Use --exclude='*.bak' to skip backup files",
            "The --visualize option shows tree structure before processing",
            "Verbosity levels: -v=info, -vv=debug, -vvv=trace",
            "Use --exclude-mode=none --include='*.py' to process only Python files",
            "The --analyze option changes how timestamps are calculated",
        ])
    
    # Pattern tips (not typically shown in examples)
    pattern_tips = [
        "Include patterns override both excludes and mode settings",
        "Use trailing slash (temp/) to match only directories",
        "Patterns use gitignore syntax: ** for recursive, ? for single char",
        "Multiple patterns can be comma-separated: --exclude='*.bak,*.tmp'",
        "Pattern matching is case-sensitive on all platforms",
    ]
    available_tips.extend(pattern_tips)
    
    # Performance tips (always useful)
    performance_tips = [
        "Large folders? Use --max-depth to limit recursion",
        "For photo archives, --strategy shallow is usually sufficient",
        "System files are skipped by default for safety and speed",
        "Use --analyze folder-only for fastest processing when appropriate",
        "Start with a small test folder before running on large directories",
    ]
    available_tips.extend(performance_tips)
    
    # Documentation tips
    doc_tips = [
        "Use --help <topic> to learn about specific features in detail",
        "Check docs/Recipes-and-Examples.md for common usage patterns",
        "See docs/Performance-Optimization.md for speed improvements",
    ]
    available_tips.extend(doc_tips)
    
    if not available_tips:
        return ""
    
    tip = random.choice(available_tips)
    return f"TIP: {tip}"


def get_tips() -> list:
    """Get all tips (for documentation purposes)."""
    return TIPS_POOL