#!/usr/bin/env python3
"""
Unit tests for the FolderScanner class.

These tests verify the core functionality of folder scanning,
timestamp calculation, and depth-based processing.
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

from folder_datetime_fix.folder_scanner import FolderScanner
from folder_datetime_fix.system_files import is_system_generated


class TestFolderScanner(unittest.TestCase):
    """Test cases for FolderScanner class."""
    
    def setUp(self):
        """Create a temporary test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_folder_scanner_')
        # Disable cache for tests to ensure consistent behavior
        self.scanner = FolderScanner(skip_generated=False, use_cache=False)
        self.scanner_skip = FolderScanner(skip_generated=True, use_cache=False)
        
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_file(self, rel_path, content='test', mtime=None):
        """Helper to create a file with specific modified time."""
        file_path = Path(self.test_dir) / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        
        if mtime:
            timestamp = mtime.timestamp()
            os.utime(file_path, (timestamp, timestamp))
        
        return file_path
    
    def test_get_folders_at_depth_0(self):
        """Test getting folders at depth 0 (base folder itself)."""
        base = Path(self.test_dir)
        folders = self.scanner.get_folders_at_depth(base, 0)
        
        self.assertEqual(len(folders), 1)
        self.assertEqual(folders[0], base)
    
    def test_get_folders_at_depth_1(self):
        """Test getting folders at depth 1 (immediate subfolders)."""
        base = Path(self.test_dir)
        
        # Create subfolders
        (base / 'folder1').mkdir()
        (base / 'folder2').mkdir()
        (base / 'folder3').mkdir()
        
        folders = self.scanner.get_folders_at_depth(base, 1)
        folder_names = [f.name for f in folders]
        
        self.assertEqual(len(folders), 3)
        self.assertIn('folder1', folder_names)
        self.assertIn('folder2', folder_names)
        self.assertIn('folder3', folder_names)
    
    def test_get_folders_at_depth_2(self):
        """Test getting folders at depth 2."""
        base = Path(self.test_dir)
        
        # Create nested structure
        (base / 'level1' / 'level2a').mkdir(parents=True)
        (base / 'level1' / 'level2b').mkdir(parents=True)
        (base / 'other').mkdir()
        
        folders = self.scanner.get_folders_at_depth(base, 2)
        folder_names = [f.name for f in folders]
        
        self.assertEqual(len(folders), 2)
        self.assertIn('level2a', folder_names)
        self.assertIn('level2b', folder_names)
    
    def test_shallow_timestamp_calculation(self):
        """Test shallow timestamp calculation (immediate children only)."""
        base = Path(self.test_dir)
        
        # Create files with different timestamps
        old_time = datetime(2024, 1, 1, 12, 0, 0)
        new_time = datetime(2024, 6, 1, 12, 0, 0)
        
        self.create_file('old.txt', mtime=old_time)
        self.create_file('new.txt', mtime=new_time)
        self.create_file('subfolder/deep.txt', mtime=datetime(2024, 12, 1))
        
        # Shallow should only see immediate children
        timestamp = self.scanner.get_shallow_timestamp(base)
        
        self.assertIsNotNone(timestamp)
        # Should match the newer file in root
        self.assertEqual(timestamp.date(), new_time.date())
    
    def test_deep_timestamp_calculation(self):
        """Test deep timestamp calculation (entire subtree)."""
        base = Path(self.test_dir)
        
        # Create nested structure with various timestamps
        old_time = datetime(2024, 1, 1)
        mid_time = datetime(2024, 6, 1)
        new_time = datetime(2024, 12, 1)
        
        self.create_file('root.txt', mtime=old_time)
        self.create_file('level1/mid.txt', mtime=mid_time)
        self.create_file('level1/level2/newest.txt', mtime=new_time)
        
        # Deep should find the newest file in entire tree
        timestamp = self.scanner.get_deep_timestamp(base)
        
        self.assertIsNotNone(timestamp)
        self.assertEqual(timestamp.date(), new_time.date())
    
    def test_system_file_exclusion(self):
        """Test that system files are excluded when skip_generated=True."""
        base = Path(self.test_dir)
        
        # Create user and system files
        user_time = datetime(2024, 6, 1)
        system_time = datetime(2024, 12, 30)
        
        self.create_file('document.txt', mtime=user_time)
        self.create_file('thumbs.db', mtime=system_time)
        self.create_file('desktop.ini', mtime=system_time)
        
        # Without skip_generated - should use newest (system file)
        timestamp_with_system = self.scanner.get_shallow_timestamp(base)
        self.assertEqual(timestamp_with_system.date(), system_time.date())
        
        # With skip_generated - should ignore system files
        timestamp_without_system = self.scanner_skip.get_shallow_timestamp(base)
        self.assertEqual(timestamp_without_system.date(), user_time.date())
    
    def test_empty_folder_returns_none(self):
        """Test that empty folders return None for timestamp."""
        base = Path(self.test_dir)
        empty_folder = base / 'empty'
        empty_folder.mkdir()
        
        timestamp = self.scanner.get_shallow_timestamp(empty_folder)
        self.assertIsNone(timestamp)
        
        timestamp = self.scanner.get_deep_timestamp(empty_folder)
        self.assertIsNone(timestamp)
    
    def test_folder_with_only_system_files(self):
        """Test folder containing only system files."""
        base = Path(self.test_dir)
        
        # Create only system files
        self.create_file('thumbs.db')
        self.create_file('.DS_Store')
        self.create_file('desktop.ini')
        
        # Without skip - should return timestamp
        timestamp = self.scanner.get_shallow_timestamp(base)
        self.assertIsNotNone(timestamp)
        
        # With skip - should return None (no user files)
        timestamp = self.scanner_skip.get_shallow_timestamp(base)
        self.assertIsNone(timestamp)
    
    def test_smart_strategy_with_subfolders(self):
        """Test smart strategy chooses deep when subfolders exist."""
        base = Path(self.test_dir)
        
        # Create structure with subfolders
        shallow_time = datetime(2024, 6, 1)
        deep_time = datetime(2024, 12, 1)
        
        self.create_file('root.txt', mtime=shallow_time)
        self.create_file('subfolder/deep.txt', mtime=deep_time)
        
        # Smart should detect subfolder and use deep strategy
        timestamp = self.scanner.get_smart_timestamp(base)
        self.assertEqual(timestamp.date(), deep_time.date())
    
    def test_smart_strategy_without_subfolders(self):
        """Test smart strategy chooses shallow when no subfolders."""
        base = Path(self.test_dir)
        
        # Create only files, no subfolders
        self.create_file('file1.txt', mtime=datetime(2024, 6, 1))
        self.create_file('file2.txt', mtime=datetime(2024, 7, 1))
        
        # Smart should use shallow strategy
        timestamp = self.scanner.get_smart_timestamp(base)
        self.assertEqual(timestamp.date(), datetime(2024, 7, 1).date())
    
    def test_scan_and_collect_multiple_depths(self):
        """Test scanning multiple depth levels."""
        base = Path(self.test_dir)
        
        # Create multi-level structure
        (base / 'level1a').mkdir()
        (base / 'level1b' / 'level2').mkdir(parents=True)
        
        results = self.scanner.scan_and_collect(base, [0, 1, 2], 'shallow')
        
        # Should have base (depth 0), 2 at depth 1, 1 at depth 2
        self.assertEqual(len(results), 4)
    
    def test_deep_strategy_fixes_intermediate_folders(self):
        """Test that deep strategy also processes intermediate folders."""
        base = Path(self.test_dir)
        
        # Create deep structure
        deep_folder = base / 'top' / 'middle' / 'bottom'
        deep_folder.mkdir(parents=True)
        
        # Add file at bottom
        self.create_file('top/middle/bottom/file.txt', mtime=datetime(2024, 9, 1))
        
        # Process top folder with deep strategy
        results = self.scanner.scan_and_collect(base, [1], 'deep')
        
        # Should include top and all intermediate folders
        paths = [str(r[0]) for r in results]
        self.assertTrue(any('top' in p and 'middle' not in p for p in paths))
        self.assertTrue(any('middle' in p and 'bottom' not in p for p in paths))
        self.assertTrue(any('bottom' in p for p in paths))


class TestSystemFileDetection(unittest.TestCase):
    """Test cases for system file detection."""
    
    def test_common_system_files(self):
        """Test detection of common system files."""
        self.assertTrue(is_system_generated('thumbs.db'))
        self.assertTrue(is_system_generated('Thumbs.db'))
        self.assertTrue(is_system_generated('desktop.ini'))
        self.assertTrue(is_system_generated('.DS_Store'))
        self.assertTrue(is_system_generated('IconCache.db'))
    
    def test_pattern_based_detection(self):
        """Test pattern-based system file detection."""
        self.assertTrue(is_system_generated('._myfile'))  # AppleDouble
        self.assertTrue(is_system_generated('~$document.docx'))  # MS Office temp
        self.assertTrue(is_system_generated('file.tmp'))
        self.assertTrue(is_system_generated('file.swp'))
        self.assertTrue(is_system_generated('~backup'))
    
    def test_user_files_not_detected(self):
        """Test that normal user files are not detected as system files."""
        self.assertFalse(is_system_generated('document.txt'))
        self.assertFalse(is_system_generated('photo.jpg'))
        self.assertFalse(is_system_generated('README.md'))
        self.assertFalse(is_system_generated('main.py'))
        self.assertFalse(is_system_generated('index.html'))
    
    def test_system_folders_detected(self):
        """Test detection of system-generated folders."""
        self.assertTrue(is_system_generated('__pycache__'))
        self.assertTrue(is_system_generated('.git'))
        self.assertTrue(is_system_generated('.vscode'))
        self.assertTrue(is_system_generated('node_modules'))
        self.assertTrue(is_system_generated('.pytest_cache'))
        self.assertTrue(is_system_generated('venv'))
        self.assertTrue(is_system_generated('build'))
        self.assertTrue(is_system_generated('dist'))
    
    def test_user_folders_not_detected(self):
        """Test that normal user folders are not detected as system folders."""
        self.assertFalse(is_system_generated('src'))
        self.assertFalse(is_system_generated('documents'))
        self.assertFalse(is_system_generated('projects'))
        self.assertFalse(is_system_generated('my_folder'))
        self.assertFalse(is_system_generated('data'))


if __name__ == '__main__':
    unittest.main()