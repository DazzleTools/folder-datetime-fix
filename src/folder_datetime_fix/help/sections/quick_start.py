"""
Quick Start section for network shares and common use cases.
"""


def get_title() -> str:
    """Get section title."""
    return "Quick Start for Network Shares"


def get_minimal(prog: str = 'fdtfix.py') -> str:
    """Get ultra-minimal version - not shown in minimal help."""
    return ""  # Don't show in minimal help


def get_short(prog: str = 'fdtfix.py') -> str:
    """Get condensed version for standard --help."""
    return f"""Quick Start for Network Shares:
  {prog} --unc-path "\\\\server\\folder" -fa --dry-run -vv  # Preview all fixes (safe)"""


def get_full(prog: str = 'fdtfix.py') -> str:
    """Get complete version with all examples."""
    return f"""Quick Start for Network Shares:
  {prog} --unc-path "\\\\server\\folder" -fa --dry-run -vv  # Preview all fixes (system files auto-skipped)
  {prog} //server/share --dry-run                          # Alternative syntax with forward slashes
  {prog} Z:\\ -fa --dry-run                                 # Mapped drive (if available)"""


def get_tips() -> list:
    """Get curated tips for quick start."""
    return [
        "Always use --dry-run first on network shares to preview changes",
        "The --unc-path option handles Windows path escaping automatically",
        "Use -vv with network operations to see progress",
    ]