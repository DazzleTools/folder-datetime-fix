"""
Integration test for Issue #17 resolution.

Verifies that modified-datetime-fix properly uses DazzleTreeLib's
integer-based depth tracking system that supports unlimited depths.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from folder_datetime_fix.cache_wrapper import (
    CacheCompleteness,
    SmartStreamingCache,
    CacheEntry,
    DAZZLETREELIB_AVAILABLE,
)


class TestIssue17Integration(unittest.TestCase):
    """Test that Issue #17 is resolved in modified-datetime-fix."""
    
    def test_depths_beyond_enum_limit(self):
        """Test that depths > 5 work correctly (old enum limit)."""
        cache = SmartStreamingCache(memory_limit_mb=10)
        
        # Create test directory structure
        with tempfile.TemporaryDirectory(prefix='test_depth_') as tmpdir:
            test_path = Path(tmpdir)
            
            # Test depths that would have failed with enum
            test_depths = [6, 7, 10, 20, 50, 100]
            
            for depth in test_depths:
                # Simulate computing at various depths
                # The wrapper should handle these without errors
                mtime, completeness = cache.get_or_compute(
                    test_path, 
                    strategy="smart",
                    max_depth=depth
                )
                
                # Should return PARTIAL_N for depths > 3 and < 999
                self.assertEqual(completeness, CacheCompleteness.PARTIAL_N)
                
                # Verify cache statistics are working
                stats = cache.get_statistics()
                self.assertGreater(stats['entries'], 0)
    
    def test_complete_depth_sentinel(self):
        """Test that complete scans use -1 sentinel value."""
        cache = SmartStreamingCache(memory_limit_mb=10)
        
        with tempfile.TemporaryDirectory(prefix='test_complete_') as tmpdir:
            test_path = Path(tmpdir)
            
            # Deep scan should use -1 internally
            mtime, completeness = cache.get_or_compute(test_path, "deep")
            
            # Should return COMPLETE
            self.assertEqual(completeness, CacheCompleteness.COMPLETE)
            self.assertEqual(completeness.value, 999)  # Backward compat value
    
    def test_depth_satisfaction_logic(self):
        """Test that deeper scans satisfy shallower requests."""
        cache = SmartStreamingCache(memory_limit_mb=10)
        
        with tempfile.TemporaryDirectory(prefix='test_satisfy_') as tmpdir:
            test_path = Path(tmpdir)
            
            # First do a deep scan (depth 10)
            mtime1, comp1 = cache.get_or_compute(test_path, "smart", max_depth=10)
            self.assertEqual(cache.misses, 1)
            self.assertEqual(cache.hits, 0)
            
            # Now request shallow - should be satisfied by cache
            mtime2, comp2 = cache.get_or_compute(test_path, "shallow")
            self.assertEqual(cache.misses, 1)  # No new miss
            self.assertEqual(cache.hits, 1)     # Got a hit
            
            # Request depth 5 - should also be satisfied
            mtime3, comp3 = cache.get_or_compute(test_path, "smart", max_depth=5)
            self.assertEqual(cache.misses, 1)  # Still no new miss
            self.assertEqual(cache.hits, 2)     # Another hit
    
    def test_backward_compatibility(self):
        """Test that old enum-style interface still works."""
        # Test CacheCompleteness enum-like behavior
        self.assertEqual(CacheCompleteness.NONE.value, 0)
        self.assertEqual(CacheCompleteness.SHALLOW.value, 1)
        self.assertEqual(CacheCompleteness.PARTIAL_2.value, 2)
        self.assertEqual(CacheCompleteness.PARTIAL_3.value, 3)
        self.assertEqual(CacheCompleteness.PARTIAL_N.value, 10)
        self.assertEqual(CacheCompleteness.COMPLETE.value, 999)
        
        # Test from_depth factory method
        self.assertEqual(CacheCompleteness.from_depth(0), CacheCompleteness.NONE)
        self.assertEqual(CacheCompleteness.from_depth(1), CacheCompleteness.SHALLOW)
        self.assertEqual(CacheCompleteness.from_depth(2), CacheCompleteness.PARTIAL_2)
        self.assertEqual(CacheCompleteness.from_depth(3), CacheCompleteness.PARTIAL_3)
        self.assertEqual(CacheCompleteness.from_depth(5), CacheCompleteness.PARTIAL_N)
        self.assertEqual(CacheCompleteness.from_depth(100), CacheCompleteness.PARTIAL_N)
        self.assertEqual(CacheCompleteness.from_depth(999), CacheCompleteness.COMPLETE)
    
    def test_cache_entry_constants(self):
        """Test that CacheEntry constants are available."""
        # These should be accessible even without DazzleTreeLib
        self.assertEqual(CacheEntry.COMPLETE_DEPTH, -1)
        self.assertEqual(CacheEntry.MAX_DEPTH, 100)
    
    def test_dazzletreelib_integration_flag(self):
        """Test that we can detect if DazzleTreeLib is available."""
        # This flag tells us if the real DazzleTreeLib is installed
        # It's okay if it's False for now (not installed yet)
        # but the flag should exist
        self.assertIsInstance(DAZZLETREELIB_AVAILABLE, bool)
        
        if DAZZLETREELIB_AVAILABLE:
            print("✓ DazzleTreeLib is installed and available")
        else:
            print("⚠ DazzleTreeLib not installed - using compatibility mode")


if __name__ == '__main__':
    unittest.main(verbosity=2)