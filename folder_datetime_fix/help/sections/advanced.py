"""
Advanced usage help section.
"""


def get_title() -> str:
    """Get section title."""
    return "Advanced Usage"


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard help."""
    return f"""Advanced Usage:
  {prog} . -fa --exclude="*.bak"                       # Skip backup files
  {prog} . --include=".git/"                           # Include normally-excluded folders
  {prog} C:\\Work --depth 2 --dry-run -vvv              # Debug output at depth 2"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Advanced Usage:
  {prog} . -fa --include-generated                     # Include system files (rare)
  {prog} . -fa --exclude="*.bak,*.tmp"                 # Skip backup and temp files
  {prog} . --include=".vscode,.vscode/**"              # Include VS Code configs
  {prog} C:\\Work --depth 2 --dry-run -vvv              # Debug output at depth 2
  {prog} C:\\Big -fa --max-depth 3                      # Limit recursion depth
  {prog} . --exclude-mode=none --include="*.py"        # Process only Python files
  {prog} . --analyze folder-only -fa                   # Use folder-only analysis"""


def get_tips() -> list:
    """Get curated tips about advanced features not obvious from examples."""
    return [
        "Patterns use gitignore syntax: ** for recursive, ? for single char",
        "Include patterns have highest priority, overriding both excludes and mode",
        "The --analyze option changes the calculation algorithm, not what's scanned",
        "Use --report to generate a detailed CSV log of all changes made",
        "Verbosity levels: -v=info, -vv=debug, -vvv=trace, -vvvv=all",
        "The --visualize option shows tree structure before any processing",
        "Combine --exclude-mode=none with --include to create a whitelist approach",
        "The --max-depth option is a safety limit, different from --depth selection",
    ]