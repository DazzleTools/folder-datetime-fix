#!/usr/bin/env python3
"""
Clean up generated files and directories to restore project to pristine state.
"""

import os
import shutil
import sys
from pathlib import Path

# Get project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Patterns to clean
CLEAN_PATTERNS = {
    'directories': [
        '__pycache__',
        '.pytest_cache',
        'build',
        'dist',
        '*.egg-info',
        '.eggs',
        '.tox',
        '.coverage',
        'htmlcov',
        '.mypy_cache',
        '.ruff_cache',
    ],
    'files': [
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.coverage',
        '.coverage.*',
        '*.cover',
        '*.log',
        '.DS_Store',
        'Thumbs.db',
        'desktop.ini',
    ]
}

def clean_project(dry_run=False):
    """Clean generated files from project."""
    
    items_removed = []
    
    # Clean directories
    for pattern in CLEAN_PATTERNS['directories']:
        for path in PROJECT_ROOT.rglob(pattern):
            if path.is_dir():
                if dry_run:
                    print(f"[DRY RUN] Would remove directory: {path.relative_to(PROJECT_ROOT)}")
                else:
                    shutil.rmtree(path)
                    print(f"Removed directory: {path.relative_to(PROJECT_ROOT)}")
                items_removed.append(path)
    
    # Clean files
    for pattern in CLEAN_PATTERNS['files']:
        for path in PROJECT_ROOT.rglob(pattern):
            if path.is_file():
                if dry_run:
                    print(f"[DRY RUN] Would remove file: {path.relative_to(PROJECT_ROOT)}")
                else:
                    path.unlink()
                    print(f"Removed file: {path.relative_to(PROJECT_ROOT)}")
                items_removed.append(path)
    
    # Summary
    if items_removed:
        print(f"\n{'Would remove' if dry_run else 'Removed'} {len(items_removed)} items")
    else:
        print("No generated files found - project is clean")
    
    return len(items_removed)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean generated files from project')
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be removed without actually removing'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    print(f"Project root: {PROJECT_ROOT}")
    
    if not args.dry_run and not args.yes:
        response = input("\nThis will remove all generated files. Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled")
            return 1
    
    num_removed = clean_project(dry_run=args.dry_run)
    return 0 if num_removed > 0 else 1

if __name__ == '__main__':
    sys.exit(main())