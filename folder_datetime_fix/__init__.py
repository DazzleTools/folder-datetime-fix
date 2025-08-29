"""
Folder DateTime Fix - Fix folder timestamps corrupted by system files.

A Python tool that restores accurate folder modified timestamps based on actual 
user file modifications, solving the Windows issue where system-generated files 
corrupt folder dates.
"""

from .version import __version__, get_version, get_base_version
from .folder_scanner import FolderScanner
from .timestamp_fixer import TimestampFixer
from .unc_handler import get_unc_handler

__all__ = [
    '__version__',
    'get_version', 
    'get_base_version',
    'FolderScanner',
    'TimestampFixer',
    'get_unc_handler',
]