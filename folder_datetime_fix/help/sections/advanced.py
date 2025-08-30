"""
Advanced usage help section with context-aware content.
"""

from ...help_system import HelpContent, HelpSection

# Define all advanced help content items for this section
ADVANCED_CONTENT = [
    HelpContent(
        id='advanced.exclude',
        command='{prog} . -fa --exclude="*.bak"',
        description='Skip backup files',
        category='advanced',
        contexts={'standard', 'full'},
        priority=10
    ),
    
    HelpContent(
        id='advanced.include_hidden',
        command='{prog} . --include=".git/"',
        description='Include normally-excluded folders',
        category='advanced',
        contexts={'standard', 'full'},
        priority=15
    ),
    
    HelpContent(
        id='advanced.debug_depth',
        command='{prog} {path} --depth 2 --dry-run -vvv',
        description='Debug output at depth 2',
        category='advanced',
        contexts={'standard', 'full'},
        priority=20,
        variables={'path': 'C:\\Work'}
    ),
    
    HelpContent(
        id='advanced.include_generated',
        command='{prog} . -fa --include-generated',
        description='Include system files (rare)',
        category='advanced',
        contexts={'full'},
        priority=25
    ),
    
    HelpContent(
        id='advanced.exclude_multiple',
        command='{prog} . -fa --exclude="*.bak,*.tmp"',
        description='Skip backup and temp files',
        category='advanced',
        contexts={'full'},
        priority=30
    ),
    
    HelpContent(
        id='advanced.include_vscode',
        command='{prog} . --include=".vscode,.vscode/**"',
        description='Include VS Code configs',
        category='advanced',
        contexts={'full'},
        priority=35
    ),
    
    HelpContent(
        id='advanced.max_depth',
        command='{prog} {path} -fa --max-depth 3',
        description='Limit recursion depth',
        category='advanced',
        contexts={'full'},
        priority=40,
        variables={'path': 'C:\\Big'}
    ),
    
    HelpContent(
        id='advanced.whitelist',
        command='{prog} . --exclude-mode=none --include="*.py"',
        description='Process only Python files',
        category='advanced',
        contexts={'full'},
        priority=45
    ),
    
    HelpContent(
        id='advanced.analyze_folder',
        command='{prog} . --analyze folder-only -fa',
        description='Use folder-only analysis',
        category='advanced',
        contexts={'full'},
        priority=50
    ),
]

# Create the section and add all items
advanced_section = HelpSection('advanced', 'Advanced Usage')
for item in ADVANCED_CONTENT:
    advanced_section.add_item(item)

# Export items for external access
ADVANCED_ITEMS = {item.id: item for item in ADVANCED_CONTENT}


def get_title() -> str:
    """Get section title."""
    return "Advanced Usage"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version - not shown in minimal help."""
    return ""  # Don't show advanced usage in minimal help


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
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