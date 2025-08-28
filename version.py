"""
Version information for the Folder DateTime Fix project.

This file is automatically updated by git pre-commit hooks.
Format: VERSION_BRANCH_BUILD-YYYYMMDD-COMMITHASH

Example: 0.5.1_main_42-20250828-a1b2c3d4

Components:
- VERSION: Semantic version (MAJOR.MINOR.PATCH)
- BRANCH: Git branch name
- BUILD: Commit count
- YYYYMMDD: Commit date
- COMMITHASH: Short commit hash
"""

# Semantic version components
MAJOR = 0
MINOR = 5
PATCH = 1

# Full version string - updated by git pre-commit hook
# DO NOT EDIT THIS LINE MANUALLY
# Note: Hash reflects the commit this version builds upon (HEAD at commit time)
# The hash will be one commit behind after the commit is created (git limitation)
__version__ = "0.5.1_private_11-20250828-960c411d"


def get_version():
    """Return the full version string including branch and build info."""
    return __version__


def get_base_version():
    """Return the semantic version string (MAJOR.MINOR.PATCH)."""
    return f"{MAJOR}.{MINOR}.{PATCH}"


def get_version_dict():
    """Return version information as a dictionary."""
    parts = __version__.split('_')
    if len(parts) >= 3:
        base_version = parts[0]
        branch = parts[1]
        # Handle remaining parts which include build-date-hash
        build_info = '_'.join(parts[2:])
        build_parts = build_info.split('-')
        
        return {
            'full': __version__,
            'base': base_version,
            'branch': branch,
            'build': build_parts[0] if len(build_parts) > 0 else '',
            'date': build_parts[1] if len(build_parts) > 1 else '',
            'commit': build_parts[2] if len(build_parts) > 2 else '',
        }
    
    # Fallback for malformed version strings
    return {
        'full': __version__,
        'base': get_base_version(),
        'branch': 'unknown',
        'build': '0',
        'date': '',
        'commit': '',
    }


# For convenience in imports
VERSION = get_version()
BASE_VERSION = get_base_version()