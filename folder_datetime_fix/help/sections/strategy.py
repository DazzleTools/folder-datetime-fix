"""
Strategy examples help section with context-aware content.
"""


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