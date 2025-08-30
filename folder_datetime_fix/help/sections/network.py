"""
Network share examples help section.
"""


def get_title() -> str:
    """Get section title."""
    return "Network Share Examples"


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard help."""
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