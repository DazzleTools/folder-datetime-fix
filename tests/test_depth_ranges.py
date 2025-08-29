"""
Test depth range functionality (--depth-to and --depth-from).
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from folder_datetime_fix.cli import parse_arguments


class TestDepthRanges(unittest.TestCase):
    """Test --depth-to and --depth-from functionality."""
    
    def test_depth_to_basic(self):
        """Test basic --depth-to functionality."""
        args = parse_arguments(['test_path', '--depth-to', '3'])
        self.assertEqual(sorted(args.depths), [0, 1, 2, 3])
    
    def test_depth_to_with_from(self):
        """Test --depth-to with --depth-from."""
        args = parse_arguments(['test_path', '--depth-from', '2', '--depth-to', '5'])
        self.assertEqual(sorted(args.depths), [2, 3, 4, 5])
    
    def test_depth_to_single(self):
        """Test --depth-to with same from and to."""
        args = parse_arguments(['test_path', '--depth-from', '3', '--depth-to', '3'])
        self.assertEqual(sorted(args.depths), [3])
    
    def test_depth_to_with_explicit_depths(self):
        """Test --depth-to combined with explicit --depth."""
        args = parse_arguments(['test_path', '--depth-to', '2', '--depth', '5', '--depth', '7'])
        self.assertEqual(sorted(args.depths), [0, 1, 2, 5, 7])
    
    def test_depth_to_zero(self):
        """Test --depth-to 0 (just root)."""
        args = parse_arguments(['test_path', '--depth-to', '0'])
        self.assertEqual(sorted(args.depths), [0])
    
    def test_depth_from_without_to(self):
        """Test that --depth-from without --depth-to doesn't create range."""
        args = parse_arguments(['test_path', '--depth-from', '3'])
        # Should default to depth 0 since no range or explicit depths specified
        self.assertEqual(sorted(args.depths), [0])
    
    def test_depth_range_validation(self):
        """Test that invalid ranges are caught."""
        with self.assertRaises(SystemExit):
            # depth-from > depth-to should error
            parse_arguments(['test_path', '--depth-from', '5', '--depth-to', '3'])
    
    def test_depth_to_large_range(self):
        """Test large depth range."""
        args = parse_arguments(['test_path', '--depth-to', '10'])
        expected = list(range(11))  # 0 through 10
        self.assertEqual(sorted(args.depths), expected)
    
    def test_depth_from_non_zero(self):
        """Test starting from non-zero depth."""
        args = parse_arguments(['test_path', '--depth-from', '3', '--depth-to', '6'])
        self.assertEqual(sorted(args.depths), [3, 4, 5, 6])
    
    def test_depth_to_with_convenience_flags(self):
        """Test that --depth-to works with convenience flags."""
        # --fix-2 should add depths 0,1
        args = parse_arguments(['test_path', '--depth-to', '3', '--fix-2'])
        # Should have 0,1,2,3 from depth-to and 0,1 from fix-2 (deduplicated)
        self.assertEqual(sorted(set(args.depths)), [0, 1, 2, 3])
    
    def test_depth_to_overrides_default(self):
        """Test that --depth-to overrides the default depth 0."""
        args = parse_arguments(['test_path', '--depth-to', '2'])
        # Should have 0,1,2 not just 0
        self.assertEqual(sorted(args.depths), [0, 1, 2])
    
    def test_depth_range_duplicates_removed(self):
        """Test that duplicate depths are removed."""
        args = parse_arguments(['test_path', '--depth-to', '2', '--depth', '1', '--depth', '2'])
        # Should deduplicate
        self.assertEqual(sorted(args.depths), [0, 1, 2])


class TestDepthRangeIntegration(unittest.TestCase):
    """Test depth ranges with actual folder processing."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_depth_range_')
        self.test_path = Path(self.test_dir)
        
        # Create a 5-level deep structure
        # depth 0: root
        # depth 1: level1/
        # depth 2: level1/level2/
        # depth 3: level1/level2/level3/
        # depth 4: level1/level2/level3/level4/
        # depth 5: level1/level2/level3/level4/level5/
        
        current = self.test_path
        for i in range(1, 6):
            current = current / f'level{i}'
            current.mkdir()
            (current / f'file{i}.txt').write_text(f'level {i}')
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_depth_range_actual_folders(self):
        """Test that depth range actually processes correct folders."""
        from folder_datetime_fix.folder_scanner import FolderScanner
        from folder_datetime_fix.analysis_strategies import StandardStrategy
        
        scanner = FolderScanner(verbose=0)
        strategy = StandardStrategy(scanner, 'shallow')
        
        # Process depths 1-3
        results = strategy.analyze(self.test_path, [1, 2, 3])
        
        # Extract depths from results
        found_depths = set()
        for folder, _ in results:
            try:
                rel = folder.relative_to(self.test_path)
                depth = len(rel.parts)
                found_depths.add(depth)
            except ValueError:
                found_depths.add(0)
        
        # Should have depths 1, 2, 3 (not 0, 4, or 5)
        self.assertEqual(found_depths, {1, 2, 3})
    
    def test_depth_to_processes_all_levels(self):
        """Test that --depth-to processes all levels in range."""
        from folder_datetime_fix.folder_scanner import FolderScanner
        from folder_datetime_fix.analysis_strategies import StandardStrategy
        
        scanner = FolderScanner(verbose=0)
        strategy = StandardStrategy(scanner, 'shallow')
        
        # Process depths 0-3 (simulating --depth-to 3)
        depths = list(range(4))  # 0, 1, 2, 3
        results = strategy.analyze(self.test_path, depths)
        
        # Should have folders at all requested depths
        found_depths = set()
        for folder, _ in results:
            try:
                rel = folder.relative_to(self.test_path)
                depth = len(rel.parts)
                found_depths.add(depth)
            except ValueError:
                found_depths.add(0)
        
        # Should have all depths 0-3
        self.assertEqual(found_depths, {0, 1, 2, 3})


if __name__ == '__main__':
    unittest.main()