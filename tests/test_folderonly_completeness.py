"""
Test cache completeness tracking specifically for FolderOnlyStrategy.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyDazzleStrategy
from dazzletreelib.testing import TestableCache


class TestFolderOnlyCompleteness(unittest.TestCase):
    """Test FolderOnlyStrategy's cache completeness behavior."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_folderonly_')
        self.test_path = Path(self.test_dir)
        
        # Create structure:
        # root/
        #   folder1/
        #     sub1/
        #       deep1/
        #     sub2/
        #   folder2/
        #     sub3/
        (self.test_path / 'folder1').mkdir()
        (self.test_path / 'folder2').mkdir()
        (self.test_path / 'folder1' / 'sub1').mkdir()
        (self.test_path / 'folder1' / 'sub2').mkdir()
        (self.test_path / 'folder2' / 'sub3').mkdir()
        (self.test_path / 'folder1' / 'sub1' / 'deep1').mkdir()
        
        # Add files
        (self.test_path / 'root.txt').write_text('test')
        (self.test_path / 'folder1' / 'file1.txt').write_text('test')
        (self.test_path / 'folder1' / 'sub2' / 'file2.txt').write_text('test')
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_completeness_tracking(self):
        """Test that completeness levels are properly set."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        
        # Scan to depth 2
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Get cache from strategy's adapter stack
        cache_adapter = strategy.adapter_stack  # This is the CompletenessAwareCacheAdapter
        testable = TestableCache(cache_adapter)
        
        # Verify cache was populated
        summary = testable.get_summary()
        self.assertGreater(summary['total_entries'], 0)
        self.assertTrue(summary['has_cache'])
        
        # Root: scanned to depth 2 (PARTIAL_2)
        self.assertTrue(testable.was_path_cached(self.test_path))
        self.assertTrue(testable.has_partial_depth(self.test_path, 2))
        
        # folder1: scanned 1 deep (SHALLOW)
        folder1 = self.test_path / 'folder1'
        self.assertTrue(testable.was_path_cached(folder1))
        self.assertTrue(testable.has_partial_depth(folder1, 1))
        
        # sub2: no subdirs, should be COMPLETE
        sub2 = self.test_path / 'folder1' / 'sub2'
        self.assertTrue(testable.was_path_cached(sub2))
        # Leaf directories are marked complete
        self.assertTrue(testable.has_partial_depth(sub2, 6))  # 6+ means COMPLETE
    
    def test_cache_reuse(self):
        """Test that cache is reused on subsequent runs."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        
        # First run
        results1 = strategy.analyze(self.test_path, [0, 1])
        
        # Check cache was populated
        cache_adapter = strategy.adapter_stack
        testable = TestableCache(cache_adapter)
        summary = testable.get_summary()
        self.assertGreater(summary['total_entries'], 0)
        
        # Second run - should use cache
        results2 = strategy.analyze(self.test_path, [0, 1])
        
        # Should get same results
        self.assertEqual(len(results1), len(results2))
        
        # Verify cache entries are reusable
        for path, _ in results1:
            self.assertTrue(testable.verify_cache_reuse(path))
    
    def test_incremental_scanning(self):
        """Test scanning incrementally deeper."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        cache_adapter = strategy.adapter_stack
        testable = TestableCache(cache_adapter)
        
        # First: shallow scan
        results1 = strategy.analyze(self.test_path, [0, 1])
        shallow_folders = set(r[0] for r in results1)
        
        # Cache should have shallow completeness for root
        self.assertTrue(testable.has_partial_depth(self.test_path, 1))
        
        # Second: deeper scan
        results2 = strategy.analyze(self.test_path, [0, 1, 2])
        all_folders = set(r[0] for r in results2)
        
        # Should have more folders
        self.assertGreater(len(all_folders), len(shallow_folders))
        
        # Root should now have deeper completeness (PARTIAL_2)
        self.assertTrue(testable.has_partial_depth(self.test_path, 2))
    
    def test_complete_folder_pruning(self):
        """Test that complete folders prune traversal."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        cache_adapter = strategy.adapter_stack
        testable = TestableCache(cache_adapter)
        
        # Create a leaf folder
        leaf = self.test_path / 'leaf_folder'
        leaf.mkdir()
        (leaf / 'file.txt').write_text('test')
        
        # First scan
        results1 = strategy.analyze(self.test_path, [0, 1])
        
        # Leaf should be marked complete (no subdirs)
        self.assertTrue(testable.was_path_cached(leaf))
        # Leaf folders with no subdirs are marked COMPLETE
        self.assertTrue(testable.has_partial_depth(leaf, 6))  # 6+ indicates COMPLETE
        
        # Second scan should reuse cached complete folder
        results2 = strategy.analyze(self.test_path, [0, 1])
        self.assertEqual(len(results1), len(results2))
        
        # Verify leaf is still cached and complete
        self.assertTrue(testable.verify_cache_reuse(leaf))
    
    def test_mixed_depths(self):
        """Test non-contiguous depth specifications."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        cache_adapter = strategy.adapter_stack
        testable = TestableCache(cache_adapter)
        
        # Scan depths 0 and 2 (skip 1)
        results = strategy.analyze(self.test_path, [0, 2])
        
        # Extract depths
        found_depths = set()
        for folder, _ in results:
            try:
                rel = folder.relative_to(self.test_path)
                depth = len(rel.parts)
            except ValueError:
                depth = 0
            found_depths.add(depth)
        
        # Should have 0 and 2, not 1
        self.assertIn(0, found_depths)
        self.assertIn(2, found_depths)
        self.assertNotIn(1, found_depths)
        
        # Verify caching worked for processed paths
        self.assertTrue(testable.was_path_cached(self.test_path))
        summary = testable.get_summary()
        self.assertGreater(summary['total_entries'], 0)


if __name__ == '__main__':
    unittest.main()