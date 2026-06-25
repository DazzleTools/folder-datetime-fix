"""
Exclusion and inclusion pattern examples with context-aware content.
"""


def get_title() -> str:
    """Get section title."""
    return "Exclusion & Inclusion Patterns"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version - not shown in minimal help."""
    return ""  # Don't show exclusion details in minimal help


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return ""  # Don't show in standard help either - it's advanced


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Exclusion & Inclusion Pattern Examples:
  {prog} . -fa --exclude="*.bak"                       # Skip all backup files
  {prog} . -fa --exclude="temp/,cache/"                # Skip temp and cache dirs
  {prog} . --exclude="**.log"                          # Skip all log files recursively
  {prog} . --include=".git/"                           # Include .git folders
  {prog} . --exclude-mode=none --include="*.py"        # Only process Python files
  {prog} . --exclude="**/node_modules/"                # Skip all node_modules dirs"""


def get_tips() -> list:
    """Get curated tips about exclusion/inclusion patterns."""
    return [
        "Patterns use gitignore syntax: * for wildcard, ** for recursive",
        "Include patterns override both exclude patterns and mode settings",
        "Use trailing slash (temp/) to match only directories",
        "Multiple patterns can be comma-separated: --exclude='*.bak,*.tmp'",
        "The --exclude-mode controls default filtering before patterns apply",
        "Pattern matching is case-sensitive on all platforms",
        "Use --exclude-mode=none with --include for whitelist-only approach",
    ]