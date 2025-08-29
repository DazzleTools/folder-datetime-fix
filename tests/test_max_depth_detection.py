"""Tests for max depth detection optimization."""

import unittest
import tempfile
import shutil
from pathlib import Path

from folder_datetime_fix.folder_scanner import FolderScanner


class TestMaxDepthDetection(unittest.TestCase):
    """Test cases for detect_max_depth functionality."""
    
    def setUp(self):
        """Create a test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_max_depth_')
        self.scanner = FolderScanner(skip_generated=True, verbose=0)
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_deep_structure(self, max_depth: int):
        """Create a directory structure with specified depth."""
        current = Path(self.test_dir)
        for i in range(max_depth):
            next_dir = current / f"level_{i+1}"
            next_dir.mkdir()
            # Also create a file at each level
            (current / f"file_{i}.txt").touch()
            current = next_dir
    
    def test_detect_shallow_tree(self):
        """Test detection of shallow tree (depth 2)."""
        base = Path(self.test_dir)
        (base / "folder1").mkdir()
        (base / "folder2").mkdir()
        (base / "folder1" / "subfolder1").mkdir()
        (base / "folder1" / "subfolder2").mkdir()
        
        detected = self.scanner.detect_max_depth(base)
        self.assertEqual(detected, 2)
    
    def test_detect_deep_tree(self):
        """Test detection of deep tree (depth 7)."""
        self.create_deep_structure(7)
        
        detected = self.scanner.detect_max_depth(Path(self.test_dir))
        self.assertEqual(detected, 7)
    
    def test_detect_empty_directory(self):
        """Test detection on empty directory."""
        detected = self.scanner.detect_max_depth(Path(self.test_dir))
        self.assertEqual(detected, 0)
    
    def test_detect_with_limit(self):
        """Test that detection respects the limit parameter."""
        self.create_deep_structure(10)
        
        # Should stop at limit
        detected = self.scanner.detect_max_depth(Path(self.test_dir), limit=5)
        self.assertEqual(detected, 5)
    
    def test_detect_irregular_tree(self):
        """Test detection on irregular tree with varying depths."""
        base = Path(self.test_dir)
        
        # Branch 1: depth 3
        branch1 = base / "branch1"
        branch1.mkdir()
        (branch1 / "level1").mkdir()
        (branch1 / "level1" / "level2").mkdir()
        (branch1 / "level1" / "level2" / "level3").mkdir()
        
        # Branch 2: depth 1
        branch2 = base / "branch2"
        branch2.mkdir()
        (branch2 / "level1").mkdir()
        
        # Branch 3: depth 5
        branch3 = base / "branch3"
        current = branch3
        for i in range(5):
            current.mkdir(parents=True, exist_ok=True)
            current = current / f"deep_{i+1}"
        current.parent.mkdir(parents=True, exist_ok=True)
        
        detected = self.scanner.detect_max_depth(base)
        self.assertEqual(detected, 5)
    
    def test_scan_with_max_depth_optimization(self):
        """Test that scan_and_collect uses max depth detection."""
        # Create structure with depth 5
        self.create_deep_structure(5)
        
        # Request depths 0-100 (simulating --fix-all)
        depths = list(range(101))
        
        # With verbose to see optimization message
        scanner = FolderScanner(skip_generated=True, verbose=1)
        results = scanner.scan_and_collect(
            Path(self.test_dir), 
            depths, 
            strategy='shallow',
            use_max_depth_detection=True
        )
        
        # Should have optimized to only scan existing depths
        # Each level should have been found
        depths_found = set()
        for folder, _ in results:
            try:
                rel = folder.relative_to(self.test_dir)
                if rel == Path('.'):
                    depth = 0
                else:
                    depth = len(rel.parts)
                depths_found.add(depth)
            except ValueError:
                pass
        
        # Should have found depths 0-5, not 0-100
        self.assertEqual(max(depths_found), 5)
    
    def test_disable_max_depth_detection(self):
        """Test that max depth detection can be disabled."""
        self.create_deep_structure(3)
        
        # Test with detection disabled
        scanner = FolderScanner(skip_generated=True, verbose=0)
        
        # This should use early termination instead of max depth detection
        depths = list(range(10))
        results = scanner.scan_and_collect(
            Path(self.test_dir),
            depths,
            strategy='shallow',
            use_max_depth_detection=False
        )
        
        # Should still work but without pre-detection
        self.assertGreater(len(results), 0)
    
    def test_system_files_ignored(self):
        """Test that system-generated folders are ignored in depth detection."""
        base = Path(self.test_dir)
        
        # Create normal structure
        normal = base / "normal"
        normal.mkdir()
        (normal / "level1").mkdir()
        
        # Create system folder that should be ignored
        system = base / "__pycache__"
        system.mkdir()
        (system / "deep1").mkdir()
        (system / "deep1" / "deep2").mkdir()
        (system / "deep1" / "deep2" / "deep3").mkdir()
        
        # With skip_generated=True, should only see depth 2 (normal path)
        scanner = FolderScanner(skip_generated=True, verbose=0)
        detected = scanner.detect_max_depth(base)
        self.assertEqual(detected, 2)
        
        # With skip_generated=False, should see depth 4 (system path)
        scanner_include = FolderScanner(skip_generated=False, verbose=0)
        detected_all = scanner_include.detect_max_depth(base)
        self.assertEqual(detected_all, 4)


if __name__ == '__main__':
    unittest.main()