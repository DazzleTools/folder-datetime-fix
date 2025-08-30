"""
Basic examples help section.
"""


def get_title() -> str:
    """Get section title."""
    return "Basic Examples"


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard help."""
    return f"""Basic Examples:
  {prog} C:\\Projects --depth 0                         # Fix only Projects folder
  {prog} C:\\Projects -f2                               # Fix folder + immediate children
  {prog} C:\\Projects -fa                               # Fix entire tree recursively
  {prog} C:\\Projects --depth-to 3                      # Process depths 0-3"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Basic Examples:
  {prog} C:\\Projects --depth 0                         # Fix only Projects folder
  {prog} C:\\Projects --depth 1                         # Fix only immediate subfolders
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