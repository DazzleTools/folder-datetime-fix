"""
Network share examples help section with context-aware content.
"""

from ...help_lib import HelpContent, HelpSection

# Define all network help content items for this section
NETWORK_CONTENT = [
    HelpContent(
        id='network.quick_start',
        command='{prog} --unc-path "\\\\server\\folder" -fa --dry-run -vv',
        description='Preview all fixes (safe)',
        category='network',
        contexts={'minimal', 'standard', 'full'},
        priority=5
    ),
    
    HelpContent(
        id='network.preview_two_level',
        command='{prog} //server/share -f2 --dry-run',
        description='Preview 2 level changes',
        category='network',
        contexts={'standard', 'full'},
        priority=10
    ),
    
    HelpContent(
        id='network.unc_progress',
        command='{prog} --unc-path "\\\\server\\folder" -fa -vv',
        description='UNC with progress info',
        category='network',
        contexts={'standard', 'full'},
        priority=15
    ),
    
    HelpContent(
        id='network.unc_preview',
        command='{prog} --unc-path "\\\\server\\folder" -fa --dry-run -vv',
        description='Preview all fixes',
        category='network',
        contexts={'full'},
        priority=20
    ),
    
    HelpContent(
        id='network.mapped_root',
        command='{prog} Z:\\ --depth 0',
        description='Fix mapped drive root',
        category='network',
        contexts={'full'},
        priority=25
    ),
    
    HelpContent(
        id='network.nas_photos',
        command='{prog} //nas/photos --strategy deep -fa',
        description='NAS photo archive fix',
        category='network',
        contexts={'full'},
        priority=30
    ),
]

# Create the section and add all items
network_section = HelpSection('network', 'Network Share Examples')
for item in NETWORK_CONTENT:
    network_section.add_item(item)

# Export items for external access
NETWORK_ITEMS = {item.id: item for item in NETWORK_CONTENT}


def get_title() -> str:
    """Get section title."""
    return "Network Share Examples"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version - not shown in minimal help."""
    return ""  # Don't show network examples in minimal help


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return f"""Network Share Examples:
  {prog} //server/share -f2 --dry-run                  # Preview 2 level changes
  {prog} --unc-path "\\\\server\\folder" -fa -vv          # UNC with progress info"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Network Share Examples:
  {prog} --unc-path "\\\\server\\folder" -fa --dry-run -vv # Preview all fixes
  {prog} //server/share -f2 --dry-run                  # Preview 2 level changes first
  {prog} --unc-path "\\\\server\\folder" -fa -vv          # UNC with progress info
  {prog} Z:\\ --depth 0                                 # Fix mapped drive root
  {prog} //nas/photos --strategy deep -fa              # NAS photo archive fix"""


def get_tips() -> list:
    """Get curated tips about network operations with practical insights."""
    return [
        "Network metadata queries are batched - deep strategy reduces round trips",
        "Use --unc-path for copy-paste from Windows Explorer to handle backslashes",
        "Mapped drives (Z:\\) can be faster than UNC paths (\\\\server\\) due to caching",
        "The tool automatically detects and optimizes for network paths",
        "High latency networks benefit from --strategy deep to minimize queries",
        "Use --max-depth on deep network shares to prevent timeout issues",
        "Forward slashes (//server/share) work as an alternative to backslashes",
    ]