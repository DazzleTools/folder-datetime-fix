"""
Timestamp fixer module for applying new timestamps to folders.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


class TimestampFixer:
    """Applies timestamp changes to folders."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize the fixer.
        
        Args:
            dry_run: If True, preview changes without applying them
            verbose: If True, provide detailed output
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.changes_made = []
        self.errors = []
    
    def fix_folder_timestamp(self, folder_path: Path, new_timestamp: datetime) -> bool:
        """
        Apply new timestamp to a folder.
        
        Args:
            folder_path: Directory to modify
            new_timestamp: New modified time to set
        
        Returns:
            True if successful, False otherwise
        """
        folder_path = Path(folder_path).resolve()
        
        try:
            # Get current timestamp for comparison
            current_mtime = datetime.fromtimestamp(folder_path.stat().st_mtime)
            
            # Check if change is needed
            if abs((current_mtime - new_timestamp).total_seconds()) < 1:
                if self.verbose:
                    print(f"No change needed for {folder_path}")
                return True
            
            if self.dry_run:
                self.changes_made.append({
                    'path': folder_path,
                    'old_time': current_mtime,
                    'new_time': new_timestamp,
                    'applied': False
                })
                if self.verbose:
                    print(f"[DRY RUN] Would change {folder_path}:")
                    print(f"  From: {current_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  To:   {new_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # Apply the new timestamp
                timestamp_seconds = new_timestamp.timestamp()
                # Set both access time and modified time
                os.utime(folder_path, (timestamp_seconds, timestamp_seconds))
                
                self.changes_made.append({
                    'path': folder_path,
                    'old_time': current_mtime,
                    'new_time': new_timestamp,
                    'applied': True
                })
                
                if self.verbose:
                    print(f"Changed {folder_path}:")
                    print(f"  From: {current_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  To:   {new_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except PermissionError as e:
            error_msg = f"Permission denied: {folder_path}"
            self.errors.append({'path': folder_path, 'error': error_msg})
            if self.verbose:
                print(f"ERROR: {error_msg}")
            return False
        
        except Exception as e:
            error_msg = f"Error fixing {folder_path}: {str(e)}"
            self.errors.append({'path': folder_path, 'error': error_msg})
            if self.verbose:
                print(f"ERROR: {error_msg}")
            return False
    
    def process_scan_results(self, scan_results: List[Tuple[Path, Optional[datetime]]]) -> dict:
        """
        Process scan results and apply timestamp fixes.
        
        Args:
            scan_results: List of (folder_path, timestamp) tuples from scanner
        
        Returns:
            Dictionary with statistics about the operation
        """
        stats = {
            'total_folders': len(scan_results),
            'folders_changed': 0,
            'folders_skipped': 0,
            'folders_error': 0,
            'empty_folders': 0
        }
        
        for folder_path, new_timestamp in scan_results:
            if new_timestamp is None:
                # No files found in folder (empty or all system files)
                stats['empty_folders'] += 1
                if self.verbose:
                    print(f"Skipping {folder_path}: No valid files found")
                continue
            
            # Try to fix the timestamp
            if self.fix_folder_timestamp(folder_path, new_timestamp):
                if not self.dry_run:
                    stats['folders_changed'] += 1
                else:
                    # In dry run, count as "would change"
                    current_mtime = datetime.fromtimestamp(folder_path.stat().st_mtime)
                    if abs((current_mtime - new_timestamp).total_seconds()) >= 1:
                        stats['folders_changed'] += 1
                    else:
                        stats['folders_skipped'] += 1
            else:
                stats['folders_error'] += 1
        
        return stats
    
    def generate_report(self) -> str:
        """
        Generate a detailed report of changes made.
        
        Returns:
            Formatted report string
        """
        report = []
        
        if self.dry_run:
            report.append("=== DRY RUN REPORT ===")
            report.append("No actual changes were made.")
        else:
            report.append("=== EXECUTION REPORT ===")
        
        report.append("")
        
        # Changes section
        if self.changes_made:
            report.append(f"Changes {'(would be) ' if self.dry_run else ''}made:")
            report.append("-" * 50)
            
            for change in self.changes_made:
                report.append(f"Folder: {change['path']}")
                report.append(f"  Old: {change['old_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                report.append(f"  New: {change['new_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                report.append("")
        else:
            report.append("No changes needed.")
        
        # Errors section
        if self.errors:
            report.append("")
            report.append("Errors encountered:")
            report.append("-" * 50)
            
            for error in self.errors:
                report.append(f"Folder: {error['path']}")
                report.append(f"  Error: {error['error']}")
                report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filepath: Path):
        """
        Save the report to a file.
        
        Args:
            filepath: Path where to save the report
        """
        report = self.generate_report()
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(report)