#!/usr/bin/env python3
"""Debug verbose argument parsing."""

import sys
from folder_datetime_fix.cli import parse_arguments

# Test parsing arguments like the CLI does
print("Testing argument parsing for -vv...")

# Simulate the exact command line args
test_args = ['.', '--dry-run', '-vv']
parser, args = parse_arguments(test_args)

print(f"args.verbose: {args.verbose}")
print(f"args.quiet: {args.quiet}")
print(f"args.verbose > 0: {args.verbose > 0}")
print(f"not args.quiet: {not args.quiet}")
print(f"args.verbose > 0 and not args.quiet: {args.verbose > 0 and not args.quiet}")

# Test UNCHandler creation with these exact parameters
from folder_datetime_fix.unc_handler import get_unc_handler

verbose_param = args.verbose > 0 and not args.quiet
print(f"\nCreating UNCHandler with verbose={verbose_param}...")

try:
    handler = get_unc_handler(verbose=verbose_param)
    print(f"SUCCESS: unctools_available = {handler.unctools_available}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()