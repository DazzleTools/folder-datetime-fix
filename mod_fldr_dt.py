#!/usr/bin/env python3
"""
Folder DateTime Fix Tool - Fixes folder modified timestamps to match their content.

This tool corrects folder timestamps that have been corrupted by system files
like thumbs.db, desktop.ini, etc. It supports depth-based processing and can
work with both local and UNC network paths.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from folder_scanner import FolderScanner
from timestamp_fixer import TimestampFixer
from unc_handler import get_unc_handler
from strategy_help import print_strategy_help
from version import __version__, get_base_version
from trace_utils import trace, set_verbosity

MAX_DEPTH_INFINITE = 100  # Reasonable maximum for "infinite" depth


@trace
def parse_arguments(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Fix folder modified timestamps to match their content (system files skipped by default)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s C:\\Projects --depth 0                    # Fix only Projects folder
  %(prog)s C:\\Projects --depth 1                    # Fix only immediate subfolders
  %(prog)s C:\\Projects --depth 0 --depth 1         # Fix Projects AND immediate subfolders
  %(prog)s C:\\Projects --depth infinite             # Fix entire tree (all depths)
  %(prog)s C:\\Projects --fix-2                      # Fix folder + immediate children
  %(prog)s \\\\server\\share --fix-all                # Fix entire tree recursively
  %(prog)s . --fix-all --include-generated         # Fix all INCLUDING system files
  %(prog)s C:\\Work --depth 2 --dry-run -v          # Preview changes at depth 2

Quick Start for Network Shares:
  %(prog)s --unc-path "\\\\server\\folder" --fix-2 --dry-run
  # Preview fixes for folder AND immediate subfolders (system files auto-skipped)

For more detailed help on specific topics:
  %(prog)s --help strategy    # Detailed explanation of shallow/deep/smart strategies
        """
    )
    
    # Version information
    parser.add_argument('--version', '-V',
                       action='version',
                       version=f'%(prog)s {__version__}',
                       help='Show program version and exit')
    
    # Path argument - either positional or via --unc-path
    parser.add_argument('path', 
                       nargs='?',
                       help='Path to process (local or UNC)')
    
    parser.add_argument('--unc-path',
                       help='UNC path with proper handling of backslashes (for copy-paste from Windows)')
    
    # Depth-based processing
    parser.add_argument('--depth', '-d',
                       action='append',
                       dest='depths',
                       help='Process folders at this depth (can be specified multiple times, or use "infinite" for all depths)')
    
    # Processing strategy
    parser.add_argument('--strategy', '-s',
                       choices=['shallow', 'deep', 'smart'],
                       default='shallow',
                       help='How to calculate timestamps (default: shallow)')
    
    # Convenience aliases
    parser.add_argument('--fix-2',
                       action='store_true',
                       help='Fix folder and immediate children (alias for: --depth 0 --depth 1 --strategy deep)')
    
    parser.add_argument('--fix-all',
                       action='store_true',
                       help='Fix entire tree recursively (alias for: --depth infinite --strategy deep)')
    
    parser.add_argument('--fix-immediate',
                       action='store_true',
                       help='Alias for: --depth 1 --strategy shallow')
    
    # System file handling
    parser.add_argument('--include-generated', '-ig',
                       action='store_true',
                       help='Include system-generated files like thumbs.db, desktop.ini (normally skipped)')
    
    # Execution modes
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview changes without applying them')
    
    parser.add_argument('--verbose', '-v',
                       action='count',
                       default=0,
                       help='Increase verbosity (-v=basic, -vv=detailed, -vvv=debug, -vvvv=trace)')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Suppress all output except errors')
    
    # Reporting
    parser.add_argument('--report', '-r',
                       type=str,
                       metavar='FILE',
                       help='Save detailed report to file')
    
    # Advanced options
    parser.add_argument('--max-depth',
                       type=int,
                       metavar='N',
                       help='Maximum depth for --fix-all or --depth infinite (default: 100)')
    
    args = parser.parse_args(argv)
    
    # Process depth arguments - handle "infinite" special case
    if args.depths:
        processed_depths = []
        for depth_str in args.depths:
            if depth_str.lower() in ['infinite', 'inf', 'all']:
                # Generate depths up to a reasonable maximum
                max_d = args.max_depth if args.max_depth else MAX_DEPTH_INFINITE
                processed_depths.extend(range(0, max_d + 1))
            else:
                try:
                    processed_depths.append(int(depth_str))
                except ValueError:
                    parser.error(f"Invalid depth value: {depth_str}. Use integers or 'infinite'")
        args.depths = processed_depths
    
    # Process convenience aliases
    if args.fix_2:
        if not args.depths:
            args.depths = []
        args.depths.extend([0, 1])
        args.strategy = 'deep'
    
    elif args.fix_all:
        # Process entire tree recursively
        max_d = args.max_depth if args.max_depth else MAX_DEPTH_INFINITE
        if not args.depths:
            args.depths = []
        args.depths.extend(range(0, max_d + 1))
        if args.strategy == 'shallow':  # Override default for tree mode
            args.strategy = 'deep'
    
    elif args.fix_immediate:
        if not args.depths:
            args.depths = []
        args.depths.append(1)
        args.strategy = 'shallow'
    
    # Default to depth 0 if no depth specified
    if not args.depths:
        args.depths = [0]
    
    # Remove duplicates and sort
    args.depths = sorted(set(args.depths))
    
    # Validate quiet and verbose aren't both set
    if args.quiet and args.verbose > 0:
        parser.error("--quiet and --verbose are mutually exclusive")
    
    return args


@trace
def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display."""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'


@trace
def print_summary(stats: dict, verbose: bool = False):
    """Print execution summary."""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total folders scanned: {stats['total_folders']}")
    print(f"Folders changed:       {stats['folders_changed']}")
    print(f"Folders skipped:       {stats['folders_skipped']}")
    print(f"Empty folders:         {stats['empty_folders']}")
    
    if stats['folders_error'] > 0:
        print(f"Folders with errors:   {stats['folders_error']} [WARNING]")
    
    print("=" * 50)


@trace
def main():
    """Main entry point."""
    # Check for special help commands first
    if len(sys.argv) >= 3 and sys.argv[1] == '--help' and sys.argv[2] == 'strategy':
        print_strategy_help()
        return 0
    
    args = parse_arguments()
    
    # Set global verbosity for tracing
    set_verbosity(args.verbose if not args.quiet else 0)
    
    # Determine which path to use
    if args.unc_path:
        # Handle UNC path with proper backslash preservation
        path_to_use = '\\\\' + args.unc_path.lstrip('\\')
    elif args.path:
        path_to_use = args.path
    else:
        # No path provided - show help
        parse_arguments(['--help'])
        return 1
    
    # Initialize UNC handler for network path support
    unc_handler = get_unc_handler(verbose=args.verbose > 0 and not args.quiet)
    
    # Convert and normalize path using UNC handler
    target_path, is_network = unc_handler.convert_for_processing(path_to_use)
    
    # Get path information
    path_info = unc_handler.get_path_info(path_to_use)
    
    # Validate path exists
    if not target_path.exists():
        print(f"ERROR: Path does not exist: {target_path}", file=sys.stderr)
        if is_network:
            print("Note: This is a network path. Check network connectivity and permissions.", file=sys.stderr)
        return 1
    
    if not target_path.is_dir():
        print(f"ERROR: Path is not a directory: {target_path}", file=sys.stderr)
        return 1
    
    # Print header
    if not args.quiet:
        print("=" * 50)
        print("Folder DateTime Fix Tool")
        print("=" * 50)
        print(f"Target:        {target_path}")
        if path_info['is_unc']:
            print(f"Type:          UNC Network Path")
        elif path_info['is_network']:
            print(f"Type:          Network Drive")
        elif path_info['is_subst']:
            print(f"Type:          Substituted Drive")
        print(f"Depths:        {args.depths}")
        print(f"Strategy:      {args.strategy}")
        print(f"System Files:  {'INCLUDED' if args.include_generated else 'SKIPPED (default)'}")
        print(f"Mode:          {'DRY RUN' if args.dry_run else 'EXECUTE'}")
        if is_network and unc_handler.unctools_available:
            print(f"UNCtools:      Enabled")
        print("=" * 50)
        print()
    
    # Initialize components
    # Default behavior is to skip system files unless --include-generated is specified
    skip_system_files = not args.include_generated
    verbosity = args.verbose if not args.quiet else 0
    scanner = FolderScanner(skip_generated=skip_system_files, verbose=verbosity)
    fixer = TimestampFixer(dry_run=args.dry_run, verbose=verbosity)
    
    # Perform scanning
    if not args.quiet:
        print("Scanning folders...")
    
    scan_results = scanner.scan_and_collect(
        target_path,
        args.depths,
        args.strategy
    )
    
    if not args.quiet:
        print(f"Found {len(scan_results)} folders to process\n")
    
    # Apply fixes
    if not args.quiet:
        action = "Previewing changes..." if args.dry_run else "Applying changes..."
        print(action)
    
    stats = fixer.process_scan_results(scan_results)
    
    # Print summary
    if not args.quiet:
        print_summary(stats, args.verbose > 0)
    
    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        fixer.save_report(report_path)
        if not args.quiet:
            print(f"\nReport saved to: {report_path}")
    
    # Print errors if any occurred
    if fixer.errors and not args.quiet:
        print("\n⚠️ Some folders could not be processed. Check permissions.")
        if args.verbose > 0:
            print("\nDetailed errors:")
            for error in fixer.errors:
                print(f"  - {error['path']}: {error['error']}")
    
    # Return appropriate exit code
    if stats['folders_error'] > 0:
        return 1  # Some errors occurred
    
    return 0  # Success


if __name__ == '__main__':
    sys.exit(main())