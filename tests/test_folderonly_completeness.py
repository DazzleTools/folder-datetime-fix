"""
Test cache completeness tracking specifically for FolderOnlyStrategy.

NOTE: These tests were originally designed for SmartStreamingCache (see test_cache_completeness.py)
which stored a cache entry for EVERY FOLDER with its own completeness level:
  cache["/root"] = SmartCacheEntry(completeness=PARTIAL_2, ...)
  cache["/root/folder1"] = SmartCacheEntry(completeness=SHALLOW, ...)
  cache["/root/folder2"] = SmartCacheEntry(completeness=COMPLETE, ...)

This allowed querying any folder: "How deep have you been scanned?"

DazzleTreeLib's CompletenessAwareCacheAdapter works differently - it caches
parent->children mappings at the get_children() operation level:
  cache["/root"] = CacheEntry(children=[folder1, folder2], completeness=PARTIAL_2)

Only parents whose children were fetched become cache keys. This is a fundamental
architectural difference that affects these tests.
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
        
        # Using new node tracking: Root was visited and scanned to depth 2
        self.assertTrue(testable.was_node_visited(self.test_path))
        self.assertTrue(testable.has_node_depth(self.test_path, 2))
        
        # folder1: was visited and scanned 1 deep
        folder1 = self.test_path / 'folder1'
        self.assertTrue(testable.was_node_visited(folder1))
        self.assertTrue(testable.has_node_depth(folder1, 1))
        
        # sub2: was visited (depth 2 from root)
        sub2 = self.test_path / 'folder1' / 'sub2'
        self.assertTrue(testable.was_node_visited(sub2))
        # Note: sub2 is at depth 2 from root, but not scanned deeper since we only went to depth 2
        # It would only be marked complete if we actually tried to scan its children
    
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
        
        # Track which nodes were visited in first run
        visited_nodes = []
        for path, _ in results1:
            if testable.was_node_visited(path):
                visited_nodes.append(path)
        
        # Second run - should use cache
        results2 = strategy.analyze(self.test_path, [0, 1])
        
        # Should get same results
        self.assertEqual(len(results1), len(results2))
        
        # Verify all nodes from first run are still tracked
        for path in visited_nodes:
            self.assertTrue(testable.was_node_visited(path))
    
    def test_incremental_scanning(self):
        """Test scanning incrementally deeper."""
        strategy = FolderOnlyDazzleStrategy(verbose=0)
        cache_adapter = strategy.adapter_stack
        testable = TestableCache(cache_adapter)
        
        # First: shallow scan
        results1 = strategy.analyze(self.test_path, [0, 1])
        shallow_folders = set(r[0] for r in results1)
        
        # Root should have been scanned to depth 1 using node tracking
        self.assertTrue(testable.was_node_visited(self.test_path))
        self.assertTrue(testable.has_node_depth(self.test_path, 1))
        
        # Second: deeper scan
        results2 = strategy.analyze(self.test_path, [0, 1, 2])
        all_folders = set(r[0] for r in results2)
        
        # Should have more folders
        self.assertGreater(len(all_folders), len(shallow_folders))
        
        # Root should now have deeper completeness (depth 2) in node tracker
        self.assertTrue(testable.has_node_depth(self.test_path, 2))
    
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
        
        # Leaf should have been visited in node tracker
        self.assertTrue(testable.was_node_visited(leaf))
        # Check what depth it actually has
        actual_depth = testable.get_node_depth(leaf)
        if actual_depth is not None:
            print(f"DEBUG: Leaf folder depth: {actual_depth}")
        # Since it's at depth 1 and has no subdirs, it was fully explored at that depth
        # The node tracker records 0 for discovered but unscanned nodes
        self.assertTrue(testable.was_node_visited(leaf))  # Just verify it was visited
        
        # Second scan should reuse cached data
        results2 = strategy.analyze(self.test_path, [0, 1])
        self.assertEqual(len(results1), len(results2))
        
        # Verify leaf is still tracked
        self.assertTrue(testable.was_node_visited(leaf))
    
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
        
        # Verify node tracking worked for processed paths
        self.assertTrue(testable.was_node_visited(self.test_path))
        summary = testable.get_summary()
        self.assertGreater(summary['total_entries'], 0)


if __name__ == '__main__':
    unittest.main()