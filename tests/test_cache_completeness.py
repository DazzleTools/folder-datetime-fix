"""Tests for cache completeness tracking system."""

import unittest
import tempfile
import shutil
from pathlib import Path
import time
import os

from folder_datetime_fix.cache_wrapper import (
    CacheCompleteness, 
    SmartCacheEntry,
    SmartStreamingCache
)


class TestCacheCompleteness(unittest.TestCase):
    """Test CacheCompleteness enum."""
    
    def test_from_depth(self):
        """Test creating completeness from depth values."""
        self.assertEqual(CacheCompleteness.from_depth(0), CacheCompleteness.NONE)
        self.assertEqual(CacheCompleteness.from_depth(1), CacheCompleteness.SHALLOW)
        self.assertEqual(CacheCompleteness.from_depth(2), CacheCompleteness.PARTIAL_2)
        self.assertEqual(CacheCompleteness.from_depth(3), CacheCompleteness.PARTIAL_3)
        self.assertEqual(CacheCompleteness.from_depth(5), CacheCompleteness.PARTIAL_N)
        self.assertEqual(CacheCompleteness.from_depth(999), CacheCompleteness.COMPLETE)
        self.assertEqual(CacheCompleteness.from_depth(1000), CacheCompleteness.COMPLETE)
    
    def test_value_ordering(self):
        """Test that completeness levels have correct ordering."""
        self.assertLess(CacheCompleteness.NONE.value, CacheCompleteness.SHALLOW.value)
        self.assertLess(CacheCompleteness.SHALLOW.value, CacheCompleteness.PARTIAL_2.value)
        self.assertLess(CacheCompleteness.PARTIAL_2.value, CacheCompleteness.PARTIAL_3.value)
        self.assertLess(CacheCompleteness.PARTIAL_3.value, CacheCompleteness.COMPLETE.value)


class TestSmartCacheEntry(unittest.TestCase):
    """Test SmartCacheEntry functionality."""
    
    def test_complete_entry_satisfies_all(self):
        """Test that complete scan satisfies all strategies."""
        entry = SmartCacheEntry(
            path=Path("/test"),
            computed_mtime=123456,
            completeness=CacheCompleteness.COMPLETE,
            actual_depth=999,
            has_subdirs=True,
            file_count=10,
            computation_time=time.time()
        )
        
        self.assertTrue(entry.satisfies("shallow"))
        self.assertTrue(entry.satisfies("deep"))
        self.assertTrue(entry.satisfies("smart"))
        self.assertTrue(entry.satisfies("shallow", 1))
        self.assertTrue(entry.satisfies("deep", 10))
    
    def test_shallow_entry_leaf_folder(self):
        """Test shallow scan of leaf folder (no subdirs) satisfies all."""
        entry = SmartCacheEntry(
            path=Path("/test"),
            computed_mtime=123456,
            completeness=CacheCompleteness.SHALLOW,
            actual_depth=1,
            has_subdirs=False,  # Leaf folder
            file_count=5,
            computation_time=time.time()
        )
        
        # Leaf folder: shallow is complete
        self.assertTrue(entry.satisfies("shallow"))
        self.assertTrue(entry.satisfies("deep"))
        self.assertTrue(entry.satisfies("smart"))
    
    def test_shallow_entry_with_subdirs(self):
        """Test shallow scan with subdirs only satisfies shallow."""
        entry = SmartCacheEntry(
            path=Path("/test"),
            computed_mtime=123456,
            completeness=CacheCompleteness.SHALLOW,
            actual_depth=1,
            has_subdirs=True,  # Has subdirectories
            file_count=5,
            computation_time=time.time()
        )
        
        self.assertTrue(entry.satisfies("shallow"))
        self.assertFalse(entry.satisfies("deep"))
        self.assertFalse(entry.satisfies("smart"))
    
    def test_partial_depth_satisfaction(self):
        """Test partial scans with different depths."""
        entry = SmartCacheEntry(
            path=Path("/test"),
            computed_mtime=123456,
            completeness=CacheCompleteness.PARTIAL_3,
            actual_depth=3,
            has_subdirs=True,
            file_count=20,
            computation_time=time.time()
        )
        
        self.assertTrue(entry.satisfies("shallow"))
        self.assertTrue(entry.satisfies("smart"))  # depth 3 satisfies smart
        self.assertFalse(entry.satisfies("deep"))
        
        # Depth requirements
        self.assertTrue(entry.satisfies("shallow", 1))
        self.assertTrue(entry.satisfies("shallow", 3))
        self.assertFalse(entry.satisfies("shallow", 5))


class TestSmartStreamingCache(unittest.TestCase):
    """Test SmartStreamingCache functionality."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test structure
        # root/
        #   file1.txt
        #   level1/
        #     file2.txt
        #     level2/
        #       file3.txt
        
        (self.test_path / "file1.txt").touch()
        (self.test_path / "level1").mkdir()
        (self.test_path / "level1" / "file2.txt").touch()
        (self.test_path / "level1" / "level2").mkdir()
        (self.test_path / "level1" / "level2" / "file3.txt").touch()
        
        # Set specific modification times
        os.utime(self.test_path / "file1.txt", (100, 100))
        os.utime(self.test_path / "level1" / "file2.txt", (200, 200))
        os.utime(self.test_path / "level1" / "level2" / "file3.txt", (300, 300))
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_cache_hit_miss(self):
        """Test cache hits and misses."""
        cache = SmartStreamingCache(memory_limit_mb=1)
        
        # First access - cache miss
        mtime1, comp1 = cache.get_or_compute(self.test_path, "shallow")
        self.assertEqual(cache.misses, 1)
        self.assertEqual(cache.hits, 0)
        
        # Second access same strategy - cache hit
        mtime2, comp2 = cache.get_or_compute(self.test_path, "shallow")
        self.assertEqual(cache.hits, 1)
        self.assertEqual(mtime1, mtime2)
        self.assertEqual(comp1, comp2)
        
        # Different strategy that shallow doesn't satisfy - cache miss
        mtime3, comp3 = cache.get_or_compute(self.test_path, "deep")
        self.assertEqual(cache.misses, 2)
    
    def test_completeness_levels(self):
        """Test different completeness levels are computed correctly."""
        cache = SmartStreamingCache(memory_limit_mb=1)
        
        # Shallow scan
        mtime_shallow, comp_shallow = cache.get_or_compute(self.test_path, "shallow")
        self.assertEqual(comp_shallow, CacheCompleteness.SHALLOW)
        self.assertEqual(mtime_shallow, 100)  # Only sees file1.txt
        
        # Deep scan (new computation)
        cache.clear()
        mtime_deep, comp_deep = cache.get_or_compute(self.test_path, "deep")
        self.assertEqual(comp_deep, CacheCompleteness.COMPLETE)
        self.assertEqual(mtime_deep, 300)  # Sees all files including file3.txt
    
    def test_deep_satisfies_shallow(self):
        """Test that deep scan result satisfies shallow requests."""
        cache = SmartStreamingCache(memory_limit_mb=1)
        
        # Do deep scan first
        mtime_deep, comp_deep = cache.get_or_compute(self.test_path, "deep")
        self.assertEqual(comp_deep, CacheCompleteness.COMPLETE)
        self.assertEqual(cache.misses, 1)
        
        # Shallow request should use cached deep result
        mtime_shallow, comp_shallow = cache.get_or_compute(self.test_path, "shallow")
        self.assertEqual(cache.hits, 1)
        self.assertEqual(mtime_shallow, mtime_deep)
        self.assertEqual(comp_shallow, CacheCompleteness.COMPLETE)
    
    def test_memory_eviction(self):
        """Test that oldest incomplete entries are evicted first."""
        cache = SmartStreamingCache(memory_limit_mb=0.001)  # Very small limit
        
        # Add multiple entries
        paths = [self.test_path / f"test{i}" for i in range(10)]
        for p in paths:
            p.mkdir(exist_ok=True)
            cache.get_or_compute(p, "shallow")
        
        # Check evictions occurred
        self.assertGreater(cache.evictions, 0)
        self.assertLess(len(cache.cache), 10)
    
    def test_statistics(self):
        """Test cache statistics tracking."""
        cache = SmartStreamingCache(memory_limit_mb=1)
        
        cache.get_or_compute(self.test_path, "shallow")
        cache.get_or_compute(self.test_path, "shallow")  # Hit
        cache.get_or_compute(self.test_path / "level1", "deep")  # Miss
        
        stats = cache.get_statistics()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 2)
        self.assertEqual(stats['entries'], 2)
        self.assertAlmostEqual(stats['hit_rate'], 1/3, places=2)


if __name__ == '__main__':
    unittest.main()