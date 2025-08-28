#!/usr/bin/env python3
"""
Unit tests for the TimestampFixer class.

These tests verify timestamp modification functionality,
dry-run mode, error handling, and reporting.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from timestamp_fixer import TimestampFixer


class TestTimestampFixer(unittest.TestCase):
    """Test cases for TimestampFixer class."""
    
    def setUp(self):
        """Create a temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix='test_timestamp_fixer_')
        self.test_folder = Path(self.test_dir) / 'test_folder'
        self.test_folder.mkdir()
        
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_fix_folder_timestamp(self):
        """Test applying new timestamp to a folder."""
        fixer = TimestampFixer(dry_run=False, verbose=False)
        
        # Set a specific timestamp
        new_time = datetime(2024, 6, 15, 14, 30, 0)
        
        # Apply the timestamp
        success = fixer.fix_folder_timestamp(self.test_folder, new_time)
        
        self.assertTrue(success)
        
        # Verify the timestamp was applied
        actual_mtime = datetime.fromtimestamp(self.test_folder.stat().st_mtime)
        # Allow small difference due to filesystem precision
        time_diff = abs((actual_mtime - new_time).total_seconds())
        self.assertLess(time_diff, 1.0)
    
    def test_dry_run_mode(self):
        """Test that dry run doesn't actually modify timestamps."""
        fixer = TimestampFixer(dry_run=True, verbose=False)
        
        # Get original timestamp
        original_mtime = self.test_folder.stat().st_mtime
        
        # Try to apply new timestamp in dry-run mode
        new_time = datetime(2024, 1, 1, 12, 0, 0)
        success = fixer.fix_folder_timestamp(self.test_folder, new_time)
        
        self.assertTrue(success)
        
        # Verify timestamp wasn't changed
        current_mtime = self.test_folder.stat().st_mtime
        self.assertEqual(original_mtime, current_mtime)
        
        # Check that change was recorded
        self.assertEqual(len(fixer.changes_made), 1)
        self.assertFalse(fixer.changes_made[0]['applied'])
    
    def test_no_change_needed(self):
        """Test handling when timestamp is already correct."""
        fixer = TimestampFixer(dry_run=False, verbose=False)
        
        # Set folder to a specific time
        target_time = datetime(2024, 6, 15, 14, 30, 0)
        timestamp_seconds = target_time.timestamp()
        os.utime(self.test_folder, (timestamp_seconds, timestamp_seconds))
        
        # Try to set same timestamp (within 1 second tolerance)
        same_time = datetime(2024, 6, 15, 14, 30, 0)
        success = fixer.fix_folder_timestamp(self.test_folder, same_time)
        
        self.assertTrue(success)
        # Should not record as a change
        self.assertEqual(len(fixer.changes_made), 0)
    
    def test_process_scan_results(self):
        """Test processing multiple scan results."""
        fixer = TimestampFixer(dry_run=False, verbose=False)
        
        # Create multiple folders
        folder1 = Path(self.test_dir) / 'folder1'
        folder2 = Path(self.test_dir) / 'folder2'
        folder3 = Path(self.test_dir) / 'folder3'
        folder1.mkdir()
        folder2.mkdir()
        folder3.mkdir()
        
        # Prepare scan results
        scan_results = [
            (folder1, datetime(2024, 1, 1)),
            (folder2, datetime(2024, 6, 1)),
            (folder3, None),  # No files found
        ]
        
        stats = fixer.process_scan_results(scan_results)
        
        self.assertEqual(stats['total_folders'], 3)
        self.assertEqual(stats['folders_changed'], 2)
        self.assertEqual(stats['empty_folders'], 1)
        self.assertEqual(stats['folders_error'], 0)
    
    def test_error_handling(self):
        """Test error handling for inaccessible folders."""
        fixer = TimestampFixer(dry_run=False, verbose=False)
        
        # Create a non-existent folder path
        fake_folder = Path(self.test_dir) / 'nonexistent'
        
        # Try to fix timestamp on non-existent folder
        success = fixer.fix_folder_timestamp(fake_folder, datetime.now())
        
        self.assertFalse(success)
        self.assertEqual(len(fixer.errors), 1)
        self.assertIn('nonexistent', str(fixer.errors[0]['path']))
    
    def test_report_generation(self):
        """Test report generation."""
        fixer = TimestampFixer(dry_run=True, verbose=False)
        
        # Process some changes
        old_time = datetime(2024, 1, 1)
        new_time = datetime(2024, 6, 1)
        
        # Record a change
        fixer.changes_made.append({
            'path': self.test_folder,
            'old_time': old_time,
            'new_time': new_time,
            'applied': False
        })
        
        # Record an error
        fixer.errors.append({
            'path': Path('/fake/path'),
            'error': 'Permission denied'
        })
        
        report = fixer.generate_report()
        
        self.assertIn('DRY RUN REPORT', report)
        self.assertIn(str(self.test_folder), report)
        self.assertIn('2024-01-01', report)
        self.assertIn('2024-06-01', report)
        self.assertIn('Permission denied', report)
    
    def test_save_report(self):
        """Test saving report to file."""
        fixer = TimestampFixer(dry_run=True, verbose=False)
        
        # Add some data
        fixer.changes_made.append({
            'path': self.test_folder,
            'old_time': datetime(2024, 1, 1),
            'new_time': datetime(2024, 6, 1),
            'applied': False
        })
        
        # Save report
        report_file = Path(self.test_dir) / 'report.txt'
        fixer.save_report(report_file)
        
        self.assertTrue(report_file.exists())
        content = report_file.read_text()
        self.assertIn('DRY RUN REPORT', content)
    
    def test_statistics_tracking(self):
        """Test that statistics are correctly tracked."""
        fixer = TimestampFixer(dry_run=False, verbose=False)
        
        # Create test folders
        folders = []
        for i in range(5):
            folder = Path(self.test_dir) / f'folder{i}'
            folder.mkdir()
            folders.append(folder)
        
        # Mix of results
        scan_results = [
            (folders[0], datetime(2024, 1, 1)),  # Will change
            (folders[1], datetime(2024, 2, 1)),  # Will change
            (folders[2], None),                   # Empty
            (folders[3], None),                   # Empty
            (folders[4], datetime(2024, 3, 1)),  # Will change
        ]
        
        stats = fixer.process_scan_results(scan_results)
        
        self.assertEqual(stats['total_folders'], 5)
        self.assertEqual(stats['folders_changed'], 3)
        self.assertEqual(stats['empty_folders'], 2)
        self.assertEqual(stats['folders_skipped'], 0)
        self.assertEqual(stats['folders_error'], 0)


class TestTimestampFixerIntegration(unittest.TestCase):
    """Integration tests for TimestampFixer with FolderScanner."""
    
    def setUp(self):
        """Create test environment."""
        self.test_dir = tempfile.mkdtemp(prefix='test_integration_')
        
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Test complete scan and fix workflow."""
        from folder_scanner import FolderScanner
        
        # Create test structure
        base = Path(self.test_dir)
        test_folder = base / 'project'
        test_folder.mkdir()
        
        # Create file with specific timestamp
        test_file = test_folder / 'document.txt'
        test_file.write_text('content')
        
        target_time = datetime(2024, 6, 15, 12, 0, 0)
        os.utime(test_file, (target_time.timestamp(), target_time.timestamp()))
        
        # Scan
        scanner = FolderScanner(skip_generated=False)
        results = scanner.scan_and_collect(base, [1], 'shallow')
        
        # Fix
        fixer = TimestampFixer(dry_run=False, verbose=False)
        stats = fixer.process_scan_results(results)
        
        # Verify
        self.assertEqual(stats['folders_changed'], 1)
        
        # Check actual timestamp
        actual_mtime = datetime.fromtimestamp(test_folder.stat().st_mtime)
        self.assertEqual(actual_mtime.date(), target_time.date())


if __name__ == '__main__':
    unittest.main()