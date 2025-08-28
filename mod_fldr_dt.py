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


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Fix folder modified timestamps to match their content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s C:\\Projects --depth 0                    # Fix only Projects folder
  %(prog)s C:\\Projects --depth 1                    # Fix only immediate subfolders
  %(prog)s C:\\Projects --depth 0 --depth 1         # Fix Projects AND immediate subfolders
  %(prog)s C:\\Projects --depth 1 --strategy deep   # Each subfolder based on entire tree
  %(prog)s \\\\server\\share --fix-all                # Fix all folders in tree (alias)
  %(prog)s . --fix-tree --skip-generated           # Fix tree, skip system files
  %(prog)s C:\\Work --depth 2 --dry-run --verbose   # Preview changes at depth 2
        """
    )
    
    # Positional argument
    parser.add_argument('path', 
                       help='Path to process (local or UNC)')
    
    # Depth-based processing
    parser.add_argument('--depth', '-d',
                       action='append',
                       type=int,
                       dest='depths',
                       help='Process folders at this depth (can be specified multiple times)')
    
    # Processing strategy
    parser.add_argument('--strategy', '-s',
                       choices=['shallow', 'deep', 'smart'],
                       default='shallow',
                       help='How to calculate timestamps (default: shallow)')
    
    # Convenience aliases
    parser.add_argument('--fix-all',
                       action='store_true',
                       help='Alias for: --depth 0 --depth 1 --strategy deep')
    
    parser.add_argument('--fix-tree',
                       action='store_true',
                       help='Process entire tree recursively')
    
    parser.add_argument('--fix-immediate',
                       action='store_true',
                       help='Alias for: --depth 1 --strategy shallow')
    
    # System file handling
    parser.add_argument('--skip-generated', '-sg',
                       action='store_true',
                       help='Skip system-generated files (thumbs.db, desktop.ini, etc.)')
    
    # Execution modes
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview changes without applying them')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Show detailed output')
    
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
                       help='Maximum depth for --fix-tree option')
    
    args = parser.parse_args()
    
    # Process convenience aliases
    if args.fix_all:
        if not args.depths:
            args.depths = []
        args.depths.extend([0, 1])
        args.strategy = 'deep'
    
    elif args.fix_tree:
        # Generate depths up to max_depth
        max_d = args.max_depth if args.max_depth else 10
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
    if args.quiet and args.verbose:
        parser.error("--quiet and --verbose are mutually exclusive")
    
    return args


def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display."""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'


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


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Convert path to Path object
    target_path = Path(args.path).resolve()
    
    # Validate path exists
    if not target_path.exists():
        print(f"ERROR: Path does not exist: {target_path}", file=sys.stderr)
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
        print(f"Depths:        {args.depths}")
        print(f"Strategy:      {args.strategy}")
        print(f"Skip System:   {args.skip_generated}")
        print(f"Mode:          {'DRY RUN' if args.dry_run else 'EXECUTE'}")
        print("=" * 50)
        print()
    
    # Initialize components
    scanner = FolderScanner(skip_generated=args.skip_generated)
    fixer = TimestampFixer(dry_run=args.dry_run, verbose=args.verbose and not args.quiet)
    
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
        print_summary(stats, args.verbose)
    
    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        fixer.save_report(report_path)
        if not args.quiet:
            print(f"\nReport saved to: {report_path}")
    
    # Print errors if any occurred
    if fixer.errors and not args.quiet:
        print("\n⚠️ Some folders could not be processed. Check permissions.")
        if args.verbose:
            print("\nDetailed errors:")
            for error in fixer.errors:
                print(f"  - {error['path']}: {error['error']}")
    
    # Return appropriate exit code
    if stats['folders_error'] > 0:
        return 1  # Some errors occurred
    
    return 0  # Success


if __name__ == '__main__':
    sys.exit(main())