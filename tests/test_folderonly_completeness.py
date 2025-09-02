"""
Test cache completeness tracking specifically for FolderOnlyStrategy.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from folder_datetime_fix.folder_scanner_dazzle import FolderScanner
from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyStrategy
from folder_datetime_fix.cache import CacheCompleteness


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
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # Scan to depth 2
        results = strategy.analyze(self.test_path, [0, 1, 2])
        
        # Check cache entries
        cache = scanner.cache.cache
        
        # Root: scanned to depth 2
        self.assertIn(self.test_path, cache)
        root_entry = cache[self.test_path]
        self.assertEqual(root_entry.completeness, CacheCompleteness.PARTIAL_2)
        
        # folder1: scanned 1 deep from its perspective
        folder1_entry = cache[self.test_path / 'folder1']
        self.assertEqual(folder1_entry.completeness, CacheCompleteness.SHALLOW)
        
        # sub2: no subdirs, should be COMPLETE
        sub2_entry = cache[self.test_path / 'folder1' / 'sub2']
        self.assertEqual(sub2_entry.completeness, CacheCompleteness.COMPLETE)
        self.assertFalse(sub2_entry.has_subdirs)
    
    def test_cache_reuse(self):
        """Test that cache is reused on subsequent runs."""
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # First run
        results1 = strategy.analyze(self.test_path, [0, 1])
        
        # Check cache was populated
        self.assertGreater(len(scanner.cache.cache), 0)
        
        # Second run - should use cache
        results2 = strategy.analyze(self.test_path, [0, 1])
        
        # Should get same results
        self.assertEqual(len(results1), len(results2))
        
        # Cache entries should be the same
        for path, _ in results1:
            self.assertIn(path, scanner.cache.cache)
    
    def test_incremental_scanning(self):
        """Test scanning incrementally deeper."""
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # First: shallow scan
        results1 = strategy.analyze(self.test_path, [0, 1])
        shallow_folders = set(r[0] for r in results1)
        
        # Cache should have shallow completeness
        root_entry = scanner.cache.cache[self.test_path]
        self.assertEqual(root_entry.completeness, CacheCompleteness.SHALLOW)
        
        # Second: deeper scan
        results2 = strategy.analyze(self.test_path, [0, 1, 2])
        all_folders = set(r[0] for r in results2)
        
        # Should have more folders
        self.assertGreater(len(all_folders), len(shallow_folders))
        
        # Root should now have deeper completeness
        root_entry_updated = scanner.cache.cache[self.test_path]
        self.assertEqual(root_entry_updated.completeness, CacheCompleteness.PARTIAL_2)
    
    def test_complete_folder_pruning(self):
        """Test that complete folders prune traversal."""
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
        # Create a leaf folder
        leaf = self.test_path / 'leaf_folder'
        leaf.mkdir()
        (leaf / 'file.txt').write_text('test')
        
        # First scan
        results1 = strategy.analyze(self.test_path, [0, 1])
        
        # Leaf should be marked complete
        leaf_entry = scanner.cache.cache[leaf]
        self.assertEqual(leaf_entry.completeness, CacheCompleteness.COMPLETE)
        
        # Second scan should reuse cached complete folder
        # (Would need to instrument to verify pruning actually happens)
        results2 = strategy.analyze(self.test_path, [0, 1])
        self.assertEqual(len(results1), len(results2))
    
    def test_mixed_depths(self):
        """Test non-contiguous depth specifications."""
        scanner = FolderScanner(use_cache=True, verbose=0)
        strategy = FolderOnlyStrategy(scanner)
        
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


if __name__ == '__main__':
    unittest.main()