"""
Detailed help topics section.
"""

from ...help_lib import HelpContent, HelpSection

# Define all detailed help topic items
DETAILED_HELP_CONTENT = [
    HelpContent(
        id='help.full',
        command='{prog} --help',
        description='Show all options and examples',
        category='help',
        contexts={'minimal', 'standard', 'full'},
        priority=10
    ),
    
    HelpContent(
        id='help.strategy',
        command='{prog} --help strategy',
        description='How scan strategies work',
        category='help',
        contexts={'minimal', 'standard', 'full'},
        priority=20
    ),
    
    HelpContent(
        id='help.analyze',
        command='{prog} --help analyze',
        description='How analysis strategies work',
        category='help',
        contexts={'minimal', 'standard', 'full'},
        priority=30
    ),
    
    HelpContent(
        id='help.patterns',
        command='{prog} --help patterns',
        description='Exclude/include patterns guide',
        category='help',
        contexts={'standard', 'full'},
        priority=40
    ),
    
    HelpContent(
        id='help.layers',
        command='{prog} --help layers',
        description='How options layer together',
        category='help',
        contexts={'standard', 'full'},
        priority=50
    ),
]

# Create the section and add all items
detailed_help_section = HelpSection('detailed_help', 'For detailed help')
for item in DETAILED_HELP_CONTENT:
    detailed_help_section.add_item(item)

# Export items for external access
DETAILED_HELP_ITEMS = {item.id: item for item in DETAILED_HELP_CONTENT}

# Legacy functions for backward compatibility
def get_title() -> str:
    """Get section title."""
    return "For detailed help on specific topics"

def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version for no-args help."""
    # Just the essentials for minimal help
    return f"""  {prog} --help                     # Show all options and examples
  {prog} --help strategy            # How scan strategies work
  {prog} --help analyze             # How analysis strategies work"""

def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return f"""For detailed help on specific topics:
  {prog} --help strategy            # How scan strategies work
  {prog} --help analyze             # How analysis strategies work
  {prog} --help patterns            # Exclude/include patterns guide
  {prog} --help layers              # How options layer together"""

def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return get_short(prog)  # Same for full in this case