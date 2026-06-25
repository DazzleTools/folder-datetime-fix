#!/usr/bin/env python3
"""
Runnable shim -- run folder-datetime-fix from a git clone WITHOUT installing,
and a backward-compat wrapper for the old mod_fldr_dt.py command.

Adds the in-repo ``src/`` to sys.path so ``python fdtfix.py ...`` works against
the local checkout (preferring local changes over any installed copy). After
``pip install``, prefer the ``fdtfix`` / ``folder-datetime-fix`` commands.
"""

import os
import sys

# Run against the in-repo src/ layout without requiring an install.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from folder_datetime_fix.cli import main

if __name__ == '__main__':
    sys.exit(main())