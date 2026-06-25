"""
Entry point for running folder_datetime_fix as a module.

This allows the package to be run with:
    python -m folder_datetime_fix
"""

from .cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())