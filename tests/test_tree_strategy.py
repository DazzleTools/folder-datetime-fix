"""
Test the TreeStrategy and FolderOnlyStrategy.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from folder_datetime_fix.folder_scanner_dazzle import FolderScanner
from folder_datetime_fix.analysis_strategies_dazzle import TreeStrategy, FolderOnlyStrategy


class TestFolderOnlyStrategy(unittest.TestCase):
    """Test the ultra-minimal folder-only strategy."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_tree_')
        self.test_path = Path(self.test_dir)
        
        # Create a simple folder structure
        (self.test_path / 'folder1').mkdir()
        (self.test_path / 'folder2').mkdir()
        (self.test_path / 'folder1' / 'subfolder1').mkdir()
        (self.test_path / 'folder1' / 'subfolder2').mkdir()
        (self.test_path / 'folder2' / 'subfolder3').mkdir()
        
        # Create some files (should be ignored by tree mode)
        (self.test_path / 'file1.txt').write_text('test')
        (self.test_path / 'folder1' / 'file2.txt').write_text('test')
        (self.test_path / 'folder1' / 'subfolder1' / 'file3.txt').write_text('test')
        
        # Create system folders (should be filtered)
        (self.test_path / '__pycache__').mkdir()
        (self.test_path / '.git').mkdir()
        (self.test_path / 'folder1' / '__pycache__').mkdir()
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_folder_only_scanning(self):
        """Test that folder-only mode computes timestamps without storing files."""
        scanner = FolderScanner(skip_generated=False, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Extract just the paths
        paths = [p for p, _ in results]
        
        # Should include all folders
        self.assertIn(self.test_path, paths)
        self.assertIn(self.test_path / 'folder1', paths)
        self.assertIn(self.test_path / 'folder2', paths)
        self.assertIn(self.test_path / 'folder1' / 'subfolder1', paths)
        self.assertIn(self.test_path / 'folder1' / 'subfolder2', paths)
        self.assertIn(self.test_path / 'folder2' / 'subfolder3', paths)
        
        # Should include system folders when not skipping
        self.assertIn(self.test_path / '__pycache__', paths)
        self.assertIn(self.test_path / '.git', paths)
        
        # Folders with files should have timestamps computed
        for path, timestamp in results:
            # The root and folder1 have files, so should have timestamps
            if path == self.test_path or path == self.test_path / 'folder1':
                self.assertIsNotNone(timestamp, f"Timestamp should be computed for {path}")
    
    def test_system_folder_filtering(self):
        """Test that system folders are filtered when skip_generated=True."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Extract just the paths
        paths = [p for p, _ in results]
        
        # Should NOT include system folders
        self.assertNotIn(self.test_path / '__pycache__', paths)
        self.assertNotIn(self.test_path / '.git', paths)
        self.assertNotIn(self.test_path / 'folder1' / '__pycache__', paths)
        
        # Should still include regular folders
        self.assertIn(self.test_path / 'folder1', paths)
        self.assertIn(self.test_path / 'folder2', paths)
    
    def test_depth_filtering(self):
        """Test that depth filtering works correctly."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # Only get depth 0 and 1
        results = strategy.analyze(self.test_path, [0, 1])
        paths = [p for p, _ in results]
        
        # Should include depth 0 and 1
        self.assertIn(self.test_path, paths)  # depth 0
        self.assertIn(self.test_path / 'folder1', paths)  # depth 1
        self.assertIn(self.test_path / 'folder2', paths)  # depth 1
        
        # Should NOT include depth 2
        self.assertNotIn(self.test_path / 'folder1' / 'subfolder1', paths)
        self.assertNotIn(self.test_path / 'folder1' / 'subfolder2', paths)
        self.assertNotIn(self.test_path / 'folder2' / 'subfolder3', paths)
    
    def test_cache_usage(self):
        """Test that folder-only mode uses cache for computed timestamps."""
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # FolderOnlyStrategy should use cache for storing results
        self.assertTrue(strategy.scanner.use_cache)
        
        # Run analysis
        results = strategy.analyze(self.test_path, [0, 1])
        
        # Should have results
        self.assertGreater(len(results), 0)
    
    def test_verbose_output(self):
        """Test that verbose mode provides statistics."""
        scanner = FolderScanner(skip_generated=True, verbose=2)
        strategy = FolderOnlyStrategy(scanner)
        
        # This should print statistics
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Should have found folders
        self.assertGreater(len(results), 0)
    
    def test_empty_directory(self):
        """Test handling of empty directory."""
        empty_dir = self.test_path / 'empty'
        empty_dir.mkdir()
        
        scanner = FolderScanner(verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        results = strategy.analyze(empty_dir, [0])
        
        # Should include the empty directory itself
        paths = [p for p, _ in results]
        self.assertIn(empty_dir, paths)
        self.assertEqual(len(results), 1)
    
    def test_strategy_metadata(self):
        """Test strategy name and description."""
        scanner = FolderScanner(verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        self.assertEqual(strategy.get_name(), "folder-only")
        self.assertIn("minimal", strategy.get_description().lower())
        self.assertIn("without storing files", strategy.get_description().lower())


class TestTreeStrategy(unittest.TestCase):
    """Test the tree strategy with bottom-up computation."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_tree_bottom_up_')
        self.test_path = Path(self.test_dir)
        
        # Create a hierarchical structure
        (self.test_path / 'folder1').mkdir()
        (self.test_path / 'folder2').mkdir()
        (self.test_path / 'folder1' / 'subfolder1').mkdir()
        (self.test_path / 'folder1' / 'subfolder2').mkdir()
        (self.test_path / 'folder2' / 'subfolder3').mkdir()
        
        # Create some files with different timestamps
        import time
        (self.test_path / 'old_file.txt').write_text('old')
        time.sleep(0.01)
        (self.test_path / 'folder1' / 'newer_file.txt').write_text('newer')
        time.sleep(0.01)
        (self.test_path / 'folder1' / 'subfolder1' / 'newest_file.txt').write_text('newest')
        
        # Create system folders (should be filtered)
        (self.test_path / '__pycache__').mkdir()
        (self.test_path / '.git').mkdir()
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_tree_structure_building(self):
        """Test that tree strategy builds proper tree structure."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        strategy = TreeStrategy(scanner)
        
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Extract just the paths
        paths = [p for p, _ in results]
        
        # Should include all non-system folders
        self.assertIn(self.test_path, paths)
        self.assertIn(self.test_path / 'folder1', paths)
        self.assertIn(self.test_path / 'folder2', paths)
        self.assertIn(self.test_path / 'folder1' / 'subfolder1', paths)
        
        # Should NOT include system folders
        self.assertNotIn(self.test_path / '__pycache__', paths)
        self.assertNotIn(self.test_path / '.git', paths)
    
    def test_bottom_up_timestamp_computation(self):
        """Test that timestamps are computed bottom-up correctly."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        strategy = TreeStrategy(scanner)
        
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Convert to dict for easier lookup
        result_dict = {path: timestamp for path, timestamp in results}
        
        # The root should have timestamp (from files)
        self.assertIsNotNone(result_dict.get(self.test_path))
        
        # folder1 should have timestamp from its newest file
        folder1_time = result_dict.get(self.test_path / 'folder1')
        self.assertIsNotNone(folder1_time)
        
        # subfolder1 should have timestamp from its file
        subfolder1_time = result_dict.get(self.test_path / 'folder1' / 'subfolder1')
        self.assertIsNotNone(subfolder1_time)
        
        # Due to bottom-up, parent folder time should be >= child folder time
        # (it includes child's newest file in its computation)
        if folder1_time and subfolder1_time:
            self.assertGreaterEqual(folder1_time, subfolder1_time)
    
    def test_tree_uses_caching(self):
        """Test that tree mode uses caching."""
        scanner = FolderScanner(use_cache=False, verbose=0)  # Start with cache off
        strategy = TreeStrategy(scanner)
        
        # TreeStrategy should enable cache for efficiency
        self.assertTrue(strategy.scanner.use_cache)
        
        results = strategy.analyze(self.test_path, [0, 1])
        self.assertGreater(len(results), 0)
    
    def test_tree_strategy_metadata(self):
        """Test tree strategy name and description."""
        scanner = FolderScanner(verbose=0)
        strategy = TreeStrategy(scanner)
        
        self.assertEqual(strategy.get_name(), "tree")
        self.assertIn("tree", strategy.get_description().lower())
        self.assertIn("bottom-up", strategy.get_description().lower())


if __name__ == '__main__':
    unittest.main()