#!/usr/bin/env python3
"""
Backward compatibility wrapper for the old mod_fldr_dt.py command.
This file allows existing scripts that call mod_fldr_dt.py to continue working.
"""

import sys
from folder_datetime_fix.cli import main

if __name__ == '__main__':
    # Run the main function from the new package
    sys.exit(main())