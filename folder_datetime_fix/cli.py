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

from .folder_scanner import FolderScanner
from .timestamp_fixer import TimestampFixer
from .unc_handler import get_unc_handler
from .strategy_help import print_strategy_help
from .analyze_help import print_analyze_help
from .version import __version__, get_base_version
from .trace_utils import trace, set_verbosity
from .analysis_strategies import StrategyFactory
from .tree_visualizer import TreeVisualizer

MAX_DEPTH_INFINITE = 100  # Reasonable maximum for "infinite" depth


def get_minimal_epilog():
    """Get minimal examples for when no path is provided."""
    # Import here to avoid circular imports
    from .help.sections import basic, tips
    
    # Just show the most essential examples
    examples = basic.get_minimal('%(prog)s')
    
    # Get a random tip - we're only showing basic examples in minimal mode
    tip = tips.get_random_tip(exclude_sections=['strategy', 'advanced', 'network', 'quick_start'])
    tip_line = f"\n{tip}" if tip else ""
    
    return f"""Quick Examples:
{examples}

For more examples: %(prog)s --help
For specific topics: %(prog)s --help <topic>{tip_line}"""


def get_standard_epilog():
    """Get standard examples for --help - shows all sections."""
    # Import sections here to avoid circular imports
    from .help.sections import quick_start, basic, strategy, advanced, network, tips
    
    sections = []
    
    # Quick Start for Network Shares
    qs = quick_start.get_short('%(prog)s')
    if qs:
        sections.append(qs)
    
    # Basic Examples
    sections.append(basic.get_short('%(prog)s'))
    
    # Strategy Examples
    sections.append(strategy.get_short('%(prog)s'))
    
    # Advanced Usage
    sections.append(advanced.get_short('%(prog)s'))
    
    # Network Share Examples
    sections.append(network.get_short('%(prog)s'))
    
    # Footer with help topics
    sections.append("""For detailed help on specific topics:
  %(prog)s --help strategy                               # How scan strategies work
  %(prog)s --help analyze                                # How analysis strategies work
  %(prog)s --help patterns                               # Exclude/include patterns guide
  %(prog)s --help layers                                 # How options layer together

See also: docs/Recipes-and-Examples.md""")
    
    # Add a random tip - we're showing all sections, so exclude none from tip selection
    # This ensures the tip doesn't duplicate what we're already showing
    tip = tips.get_random_tip(exclude_sections=['basic', 'strategy', 'advanced', 'network', 'quick_start'])
    if tip:
        sections.append(tip)
    
    return '\n\n'.join(sections)


def create_parser(show_full_help=False):
    """Create the argument parser with appropriate epilog and all arguments."""
    epilog = get_standard_epilog() if show_full_help else get_minimal_epilog()
    
    parser = argparse.ArgumentParser(
        description='Fix folder modified timestamps to match their content (system files skipped by default)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
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
    
    # Depth range specification (easier than multiple --depth)
    parser.add_argument('--depth-to',
                       type=int,
                       metavar='N',
                       help='Process all depths from 0 to N inclusive (e.g., --depth-to 3 means depths 0,1,2,3)')
    
    parser.add_argument('--depth-from',
                       type=int,
                       default=0,
                       metavar='N', 
                       help='Start depth range from N (default: 0, use with --depth-to)')
    
    # Processing strategy
    parser.add_argument('--strategy', '-s',
                       choices=['shallow', 'deep', 'smart'],
                       default='shallow',
                       help='How to calculate timestamps (default: shallow)')
    
    # Convenience aliases
    parser.add_argument('--fix-2', '-f2',
                       action='store_true',
                       help='Fix folder and immediate children (alias for: --depth 0 --depth 1 --strategy deep)')
    
    parser.add_argument('--fix-all', '-fa',
                       action='store_true',
                       help='Fix entire tree recursively (alias for: --depth infinite --strategy deep)')
    
    parser.add_argument('--fix-immediate', '--fix-1', '-f1',
                       action='store_true',
                       help='Fix immediate subfolders only (alias for: --depth 1 --strategy shallow)')
    
    # Advanced exclusion control
    exclusion_group = parser.add_argument_group('Exclusion Control')
    
    exclusion_group.add_argument('--exclude-mode',
                                 choices=['default', 'none', 'files', 'folders'],
                                 default='default',
                                 help='Base exclusion mode: default=skip system files/folders, '
                                      'none=include everything, files=skip system files only, '
                                      'folders=skip system folders only')
    
    exclusion_group.add_argument('--exclude',
                                 metavar='PATTERNS',
                                 help='Comma-separated glob patterns to exclude '
                                      '(e.g., "*.tmp,*.bak,build/,**/*.cache")')
    
    exclusion_group.add_argument('--include',
                                 metavar='PATTERNS',
                                 help='Comma-separated glob patterns to include, overrides excludes '
                                      '(e.g., ".vscode/settings.json,.git/config")')
    
    # Legacy compatibility
    exclusion_group.add_argument('--include-generated', '-ig',
                                 action='store_true',
                                 help='(Legacy) Include all system-generated files - same as --exclude-mode=none')
    
    # Analysis mode
    parser.add_argument('--analyze',
                       default='auto',
                       help='Analysis strategy: tree (full memory), folder-only (minimal), '
                            'low-memory (streaming), auto (adaptive), or comma-separated options '
                            'like tree,ctime (default: auto)')
    
    # Output control
    parser.add_argument('--visualize',
                       action='store_true',
                       help='Show visual tree structure of what will be processed (debug mode)')
    
    parser.add_argument('--dry-run', '-n',
                       action='store_true',
                       help='Preview changes without applying them')
    
    parser.add_argument('--verbose', '-v',
                       action='count',
                       default=0,
                       help='Increase verbosity (-v=basic info, -vv=detailed, -vvv=debug with tree view, -vvvv=trace)')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Suppress all output except errors')
    
    parser.add_argument('--report', '-r',
                       metavar='FILE',
                       help='Save detailed report to file')
    
    # Performance limits
    parser.add_argument('--max-depth', '-m',
                       type=int,
                       default=MAX_DEPTH_INFINITE,
                       metavar='N',
                       help=f'Maximum depth for --fix-all or --depth infinite (default: {MAX_DEPTH_INFINITE})')
    
    return parser


@trace
def parse_arguments(argv=None):
    """Parse command-line arguments."""
    # Determine if user is asking for full help
    # Check both argv and sys.argv to catch all cases
    import sys
    show_full_help = (argv and '--help' in argv) or (not argv and '--help' in sys.argv)
    
    # Create parser with appropriate epilog and all arguments
    parser = create_parser(show_full_help)
    
    # Parse the arguments
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
    
    # Process depth range (--depth-to and --depth-from)
    if args.depth_to is not None:
        if not args.depths:
            args.depths = []
        
        # Validate range
        if args.depth_from > args.depth_to:
            parser.error(f"--depth-from ({args.depth_from}) cannot be greater than --depth-to ({args.depth_to})")
        
        # Add the range
        depth_range = range(args.depth_from, args.depth_to + 1)
        args.depths.extend(depth_range)
        
        if args.verbose >= 1:
            print(f"Depth range expanded: {args.depth_from} to {args.depth_to} = {list(depth_range)}")
    
    # Process convenience aliases
    if args.fix_2:
        if not args.depths:
            args.depths = [0, 1]
        else:
            args.depths.extend([0, 1])
        args.strategy = 'deep'
        
    if args.fix_all:
        # Generate depths up to max_depth
        max_d = args.max_depth if args.max_depth else MAX_DEPTH_INFINITE
        args.depths = list(range(0, max_d + 1))
        args.strategy = 'deep'
        
    if args.fix_immediate:
        if not args.depths:
            args.depths = [1]
        else:
            args.depths.append(1)
        args.strategy = 'shallow'
    
    # Set default depths if none specified
    if not args.depths:
        args.depths = [0]  # Default to current folder only
    
    # Remove duplicates and sort
    args.depths = sorted(set(args.depths))
    
    # Validate quiet and verbose aren't both set
    if args.quiet and args.verbose > 0:
        parser.error("--quiet and --verbose are mutually exclusive")
    
    return parser, args


@trace
def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display."""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'


def _count_tree_nodes(node) -> int:
    """Count total nodes in a tree structure."""
    if not node:
        return 0
    count = 1
    for child in node.children:
        count += _count_tree_nodes(child)
    return count


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
    if len(sys.argv) >= 3 and sys.argv[1] == '--help':
        if sys.argv[2] == 'strategy':
            print_strategy_help()
            return 0
        elif sys.argv[2] == 'analyze':
            print_analyze_help()
            return 0
    
    parser, args = parse_arguments()
    
    # Set global verbosity for tracing
    set_verbosity(args.verbose if not args.quiet else 0)
    
    # Determine which path to use
    if args.unc_path:
        # Handle UNC path with proper backslash preservation
        path_to_use = '\\\\' + args.unc_path.lstrip('\\')
    elif args.path:
        path_to_use = args.path
    else:
        # No path provided - show help using the parser we already created
        parser.print_help()
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
    
    # Handle legacy --include-generated flag BEFORE printing header
    if args.include_generated:
        if args.exclude_mode == 'default':
            args.exclude_mode = 'none'
            if args.verbose > 0 and not args.quiet:
                print("Note: --include-generated is deprecated. Use --exclude-mode=none")
    
    # Print header
    if not args.quiet:
        print("=" * 50)
        print("Folder DateTime Fix Tool")
        print("=" * 50)
        print(f"Target:        {target_path}")
        if path_info['is_unc']:
            print(f"Type:          UNC Network Path")
        elif path_info['is_substituted']:
            print(f"Type:          Substituted Drive")
        print(f"Depths:        {args.depths}")
        print(f"Strategy:      {args.strategy}")
        print(f"Exclusions:    Mode={args.exclude_mode}", end="")
        if args.exclude:
            print(f", Exclude={args.exclude[:30]}{'...' if len(args.exclude) > 30 else ''}", end="")
        if args.include:
            print(f", Include={args.include[:30]}{'...' if len(args.include) > 30 else ''}", end="")
        print()
        print(f"Mode:          {'DRY RUN' if args.dry_run else 'EXECUTE'}")
        if is_network and unc_handler.unctools_available:
            print(f"UNCtools:      Enabled")
        print("=" * 50)
        print()
    
    # Create exclusion filter
    from .exclusion_filter import ExclusionFilter
    
    exclusion_filter = ExclusionFilter.from_args(
        mode=args.exclude_mode,
        exclude=args.exclude,
        include=args.include
    )
    
    # For backward compatibility in visualization
    skip_system_files = (args.exclude_mode == 'default')
    
    # Handle visualization mode
    if args.visualize:
        if not args.quiet:
            print("Generating folder structure visualization...")
            print()
        
        # Create visualizer
        visualizer = TreeVisualizer(
            max_depth=max(args.depths) if args.depths else 10,
            skip_system_files=skip_system_files,
            verbose=args.verbose
        )
        
        # Generate and display tree
        tree = visualizer.build_tree(target_path)
        if tree:
            output = visualizer.format_tree(tree)
            print(output)
            
            # Show statistics
            stats = visualizer.get_statistics(tree)
            print("\n" + "=" * 50)
            print("VISUALIZATION STATISTICS")
            print("=" * 50)
            print(f"Total folders:     {stats['total_folders']}")
            print(f"Total files:       {stats['total_files']}")
            print(f"Max depth:         {stats['max_depth']}")
            print(f"Depths to process: {args.depths}")
            
            # Count nodes at each depth
            depth_counts = {}
            for depth in args.depths:
                count = visualizer.count_folders_at_depth(tree, depth)
                if count > 0:
                    depth_counts[depth] = count
            
            if depth_counts:
                print("\nFolders at each depth:")
                for depth, count in sorted(depth_counts.items()):
                    print(f"  Depth {depth}: {count} folders")
            
            print("=" * 50)
        
        # Exit after visualization
        return 0
    
    # Initialize components
    verbosity = args.verbose if not args.quiet else 0
    scanner = FolderScanner(exclusion_filter=exclusion_filter, verbose=verbosity)
    fixer = TimestampFixer(dry_run=args.dry_run, verbose=verbosity)
    
    # Create analysis strategy based on --analyze parameter
    analysis_strategy = StrategyFactory.create_strategy(
        args.analyze,
        verbose=verbosity
    )
    
    # If verbose, show analysis strategy info
    if verbosity >= 1 and not args.quiet:
        strategy_info = analysis_strategy.get_info()
        print(f"Analysis:      {strategy_info['name']}")
        if strategy_info.get('description'):
            print(f"               {strategy_info['description']}")
        print()
    
    # Track overall statistics
    total_stats = {
        'total_folders': 0,
        'folders_changed': 0,
        'folders_skipped': 0,
        'empty_folders': 0,
        'folders_error': 0
    }
    
    # Report file setup
    report_file = None
    if args.report:
        try:
            report_file = open(args.report, 'w', encoding='utf-8')
            report_file.write(f"Folder DateTime Fix Report\n")
            report_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write(f"Target: {target_path}\n")
            report_file.write(f"Depths: {args.depths}\n")
            report_file.write(f"Strategy: {args.strategy}\n")
            report_file.write(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}\n")
            report_file.write("\n")
            report_file.write("Path,Original Time,New Time,Status\n")
        except Exception as e:
            print(f"Warning: Could not create report file: {e}", file=sys.stderr)
            report_file = None
    
    try:
        # Scan folders at specified depths
        if not args.quiet:
            print("Scanning folders...")
        
        folders_to_process = scanner.scan_at_depths(target_path, args.depths, args.strategy)
        
        if not args.quiet:
            print(f"Found {len(folders_to_process)} folders to process\n")
        
        # Analyze folders using the selected strategy
        if not args.quiet:
            if args.dry_run:
                print("Previewing changes...")
            else:
                print("Applying changes...")
            print()
        
        # Process folders with analysis strategy
        analysis_results = analysis_strategy.analyze(folders_to_process, scanner, args.strategy)
        
        # Apply fixes based on analysis results
        for folder_path, timestamps in analysis_results.items():
            if folder_path in folders_to_process:
                original_time = folders_to_process[folder_path]
                
                # Determine if change is needed
                if timestamps and timestamps.get('newest'):
                    new_time = timestamps['newest']
                    
                    # Check if times differ
                    if original_time != new_time:
                        # Apply the fix
                        success = fixer.fix_folder_timestamp(folder_path, new_time)
                        
                        if success:
                            total_stats['folders_changed'] += 1
                            status = "CHANGED"
                        else:
                            total_stats['folders_error'] += 1
                            status = "ERROR"
                        
                        # Show verbose output
                        if verbosity >= 1 and not args.quiet:
                            print(f"{'[DRY RUN] ' if args.dry_run else ''}{folder_path}")
                            print(f"  Original: {format_timestamp(original_time)}")
                            print(f"  New:      {format_timestamp(new_time)}")
                            print(f"  Status:   {status}")
                            print()
                    else:
                        total_stats['folders_skipped'] += 1
                        status = "SKIPPED"
                        
                        if verbosity >= 2 and not args.quiet:
                            print(f"{folder_path}")
                            print(f"  Status:   {status} (already correct)")
                            print()
                else:
                    # Empty folder or no valid timestamps
                    total_stats['empty_folders'] += 1
                    status = "EMPTY"
                    
                    if verbosity >= 2 and not args.quiet:
                        print(f"{folder_path}")
                        print(f"  Status:   {status} (no files)")
                        print()
                
                # Write to report file
                if report_file:
                    orig_str = format_timestamp(original_time) if original_time else "N/A"
                    new_str = format_timestamp(timestamps.get('newest')) if timestamps and timestamps.get('newest') else "N/A"
                    report_file.write(f'"{folder_path}","{orig_str}","{new_str}","{status}"\n')
                
                total_stats['total_folders'] += 1
        
        # Add strategy-specific statistics
        strategy_stats = analysis_strategy.get_statistics()
        if strategy_stats:
            total_stats.update(strategy_stats)
        
        # Print summary
        if not args.quiet:
            print_summary(total_stats, verbose=verbosity >= 1)
        
        # Close report file
        if report_file:
            report_file.write(f"\nSummary:\n")
            report_file.write(f"Total folders: {total_stats['total_folders']}\n")
            report_file.write(f"Changed: {total_stats['folders_changed']}\n")
            report_file.write(f"Skipped: {total_stats['folders_skipped']}\n")
            report_file.write(f"Empty: {total_stats['empty_folders']}\n")
            if total_stats['folders_error'] > 0:
                report_file.write(f"Errors: {total_stats['folders_error']}\n")
            report_file.close()
            
            if not args.quiet:
                print(f"\nReport saved to: {args.report}")
        
        # Return exit code based on errors
        return 1 if total_stats['folders_error'] > 0 else 0
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if verbosity >= 3:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())