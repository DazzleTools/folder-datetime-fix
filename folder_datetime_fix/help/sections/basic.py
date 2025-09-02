"""
Basic examples help section with context-aware content.
"""

from ...help_lib import HelpContent, HelpSection

# Define all basic help content items for this section
BASIC_CONTENT = [
    HelpContent(
        id='basic.f2',
        command='{prog} . -f2',
        description='Fix current + immediate children',
        category='basic',
        contexts={'minimal', 'standard', 'full', 'tutorial'},
        priority=10
    ),
    
    HelpContent(
        id='basic.f2_with_path',
        command='{prog} {path} -f2',
        description='Fix folder + immediate children',
        category='basic',
        contexts={'standard', 'full'},
        priority=12,
        variables={'path': 'C:\\Projects'}
    ),
    
    HelpContent(
        id='basic.dry_run',
        command='{prog} . -fa --dry-run',
        description='Preview all changes (safe)',
        category='basic',
        contexts={'minimal', 'standard', 'full', 'error', 'tutorial'},
        priority=5
    ),
    
    HelpContent(
        id='basic.recursive',
        command='{prog} {path} -fa',
        description='Fix entire tree recursively',
        category='basic',
        contexts={'minimal', 'standard', 'full', 'tutorial'},
        priority=15,
        variables={'path': 'C:\\Projects'}
    ),
    
    HelpContent(
        id='basic.depth_only_root',
        command='{prog} . --depth 0',
        description='Fix root folder only (no children)',
        category='basic',
        contexts={'standard', 'full'},
        priority=20
    ),
    
    HelpContent(
        id='basic.depth_only_immediate',
        command='{prog} . -f1',
        description='Fix immediate children only',
        category='basic',
        contexts={'standard', 'full'},
        priority=25
    ),
    
    HelpContent(
        id='basic.depth_both',
        command='{prog} . --depth 0 --depth 1',
        description='Fix root and immediate children',
        category='basic',
        contexts={'standard', 'full'},
        priority=30
    ),
    
    HelpContent(
        id='basic.depth_to',
        command='{prog} . --depth-to 3',
        description='Fix from root down to depth 3',
        category='basic',
        contexts={'minimal', 'full'},
        priority=35
    ),
    
    HelpContent(
        id='basic.depth_range',
        command='{prog} . --depth-from 2 --depth-to 5',
        description='Fix only depths 2 through 5',
        category='basic',
        contexts={'full'},
        priority=40
    ),
]

# Create the section and add all items
basic_section = HelpSection('basic', 'Basic Examples')
for item in BASIC_CONTENT:
    basic_section.add_item(item)

# Export items for external access
BASIC_ITEMS = {item.id: item for item in BASIC_CONTENT}


def get_title() -> str:
    """Get section title."""
    return "Basic Examples"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version for no-args help (2-3 examples max)."""
    return f"""  {prog} . -f2                # Fix current + immediate children
  {prog} . -fa --dry-run      # Preview all changes (safe)
  {prog} C:\\Projects -fa      # Fix entire tree recursively"""


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return f"""Basic Examples:
  {prog} C:\\Projects --depth 0                         # Fix only Projects folder
  {prog} C:\\Projects -f2                               # Fix folder + immediate children
  {prog} C:\\Projects -fa                               # Fix entire tree recursively
  {prog} C:\\Code --depth-to 3                          # Process depths 0-3"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples (for --help examples or similar)."""
    return f"""Basic Examples:
  {prog} C:\\Projects --depth 0                         # Fix only Projects folder
  {prog} C:\\Projects --depth 1                         # Fix only immediate subfolders (short: -f1)
  {prog} C:\\Projects --depth 0 --depth 1               # Fix Projects AND immediate subfolders
  {prog} C:\\Projects -f2                               # Shortcut for above (folder + children)
  {prog} C:\\Projects -fa                               # Fix entire tree recursively
  {prog} C:\\Code --depth-to 3                          # Process depths 0-3 (simpler than 4x --depth)
  {prog} C:\\Projects --depth-from 1 --depth-to 4       # Process depths 1-4 only"""


def get_tips() -> list:
    """Get curated tips related to basic usage that aren't obvious from examples."""
    return [
        "The --depth-to option automatically includes all depths from 0 to N",
        "Combining multiple --depth values lets you skip intermediate levels",
        "The -f2 shortcut is equivalent to --depth 0 --depth 1 --strategy deep",
        "Folder timestamps reflect the newest item inside, including system files",
        "Use . (dot) to process the current directory without typing the full path",
    ]