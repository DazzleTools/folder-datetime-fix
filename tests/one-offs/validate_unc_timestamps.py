#!/usr/bin/env python3
"""
Validation script to understand timestamp discrepancies in UNC paths.
This helps us validate both DazzleTreeLib's traversal and modified_datetime_fix's calculations.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def check_folder_contents(folder_path):
    """Check all files in a folder including hidden/system files."""
    folder_path = Path(folder_path)
    print(f"\nChecking: {folder_path}")
    print("=" * 80)
    
    if not folder_path.exists():
        print(f"ERROR: Path does not exist: {folder_path}")
        return
        
    # Get folder's own timestamp
    folder_stat = folder_path.stat()
    folder_mtime = datetime.fromtimestamp(folder_stat.st_mtime)
    print(f"Folder Modified Time: {folder_mtime}")
    print()
    
    # List ALL files including hidden
    all_items = []
    newest_file_time = None
    newest_file_name = None
    
    try:
        for item in folder_path.iterdir():
            item_stat = item.stat()
            item_mtime = datetime.fromtimestamp(item_stat.st_mtime)
            
            # Track newest file (not folder)
            if item.is_file():
                if newest_file_time is None or item_mtime > newest_file_time:
                    newest_file_time = item_mtime
                    newest_file_name = item.name
            
            all_items.append((item.name, item_mtime, item.is_dir()))
    except Exception as e:
        print(f"ERROR accessing folder: {e}")
        return
    
    # Sort by modification time descending
    all_items.sort(key=lambda x: x[1], reverse=True)
    
    print("All items (sorted by newest first):")
    print("-" * 80)
    for name, mtime, is_dir in all_items[:20]:  # Show top 20
        type_str = "[DIR] " if is_dir else "[FILE]"
        print(f"{type_str} {mtime} - {name}")
    
    if len(all_items) > 20:
        print(f"... and {len(all_items) - 20} more items")
    
    print()
    print("Analysis:")
    print("-" * 80)
    print(f"Total items: {len(all_items)}")
    print(f"Newest file: {newest_file_name} at {newest_file_time}")
    print(f"Folder time: {folder_mtime}")
    
    if newest_file_time and folder_mtime < newest_file_time:
        print(f"WARNING: Folder is OLDER than its newest file by {newest_file_time - folder_mtime}")
        print(f"   This is what modified_datetime_fix should fix!")
    else:
        print("OK: Folder timestamp is already correct (newer than all files)")
    
    # Check for system files
    system_files = []
    for name, mtime, is_dir in all_items:
        if not is_dir:
            lower_name = name.lower()
            if any(pattern in lower_name for pattern in ['index.db', 'thumbs.db', 'desktop.ini', '.ds_store']):
                system_files.append((name, mtime))
    
    if system_files:
        print()
        print("System/Index files found (normally ignored by modified_datetime_fix):")
        for name, mtime in system_files:
            print(f"  - {name}: {mtime}")


def main():
    """Main validation function."""
    # Test paths
    paths_to_check = [
        r"\\aktuldjr\j\maisie-proj-org",
        r"\\aktuldjr\j\maisie-proj-org\Memorial Day Weekend shots",
        r"\\aktuldjr\j\maisie-proj-org\Memorial Day Weekend shots\gens",
        r"\\aktuldjr\j\maisie-proj-org\mit sitting",
        r"\\aktuldjr\j\maisie-proj-org\openart.ai",
    ]
    
    print("UNC Path Timestamp Validation")
    print("=" * 80)
    print("This script checks actual filesystem timestamps to validate our tool's behavior")
    print()
    
    for path in paths_to_check:
        check_folder_contents(path)
        print()
    
    print("\nValidation Summary:")
    print("=" * 80)
    print("The timestamps reported by modified_datetime_fix appear to be including")
    print("system-generated files (like index.db, Thumbs.db) that have newer dates.")
    print("This is actually INCORRECT behavior - our tool should ignore these files.")
    print()
    print("The discrepancy suggests there might be an issue with:")
    print("1. How DazzleTreeLib's file adapter reports file timestamps, OR")
    print("2. How our exclusion filter is being applied during timestamp calculation")


if __name__ == "__main__":
    main()