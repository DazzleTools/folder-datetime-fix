"""
Strategy examples help section with context-aware content.
"""

from ...help_lib import HelpContent, HelpSection

# Define all strategy help content items for this section
STRATEGY_CONTENT = [
    HelpContent(
        id='strategy.shallow',
        command='{prog} {path} --strategy shallow',
        description='Quick scan, immediate files only',
        category='strategy',
        contexts={'minimal', 'standard', 'full'},
        priority=10,
        variables={'path': 'C:\\Photos'}
    ),
    
    HelpContent(
        id='strategy.deep',
        command='{prog} {path} --strategy deep',
        description='Full recursive scan for accuracy',
        category='strategy',
        contexts={'minimal', 'standard', 'full'},
        priority=15,
        variables={'path': 'C:\\Projects'}
    ),
    
    HelpContent(
        id='strategy.smart',
        command='{prog} {path} --strategy smart',
        description='Auto-choose based on structure',
        category='strategy',
        contexts={'standard', 'full'},
        priority=20,
        variables={'path': 'C:\\Work'}
    ),
    
    HelpContent(
        id='strategy.deep_limited',
        command='{prog} {path} --depth-to 2 --strategy deep',
        description='Deep scan but limited depth',
        category='strategy',
        contexts={'full'},
        priority=25,
        variables={'path': 'C:\\Archive'}
    ),
    
    HelpContent(
        id='strategy.smart_recursive',
        command='{prog} . -fa --strategy smart',
        description='Smart strategy for entire tree',
        category='strategy',
        contexts={'full'},
        priority=30
    ),
]

# Create the section and add all items
strategy_section = HelpSection('strategy', 'Strategy Examples (shallow/deep/smart)')
for item in STRATEGY_CONTENT:
    strategy_section.add_item(item)

# Export items for external access
STRATEGY_ITEMS = {item.id: item for item in STRATEGY_CONTENT}


def get_title() -> str:
    """Get section title."""
    return "Strategy Examples"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version - not shown in minimal help."""
    return ""  # Don't show strategies in minimal help


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return f"""Strategy Examples (shallow/deep/smart):
  {prog} C:\\Photos --strategy shallow                  # Quick scan, immediate files only
  {prog} C:\\Projects --strategy deep                   # Full recursive scan for accuracy
  {prog} C:\\Work --strategy smart                      # Auto-choose based on structure"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Strategy Examples (shallow/deep/smart):
  {prog} C:\\Photos --strategy shallow                  # Quick scan, immediate files only
  {prog} C:\\Projects --strategy deep                   # Full recursive scan for accuracy
  {prog} C:\\Work --strategy smart                      # Auto-choose based on structure
  {prog} C:\\Archive --depth-to 2 --strategy deep      # Deep scan but limited depth
  {prog} . -fa --strategy smart                        # Smart strategy for entire tree"""


def get_tips() -> list:
    """Get curated tips about strategies that provide deeper insights."""
    return [
        "The 'shallow' strategy only looks at immediate children, making it fast but less accurate",
        "The 'smart' strategy checks folder structure first, then decides between shallow and deep",
        "Strategy affects accuracy: shallow=fast/approximate, deep=slow/precise",
        "Network shares benefit from deep strategy due to metadata caching",
        "The strategy applies at each depth level independently",
        "Using --strategy smart with --max-depth prevents runaway recursion",
    ]