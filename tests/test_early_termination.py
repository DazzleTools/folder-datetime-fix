"""
Test early termination optimization for deep folder scanning.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from folder_datetime_fix.folder_scanner import FolderScanner


class TestEarlyTermination(unittest.TestCase):
    """Test that folder scanning terminates early when no folders found."""
    
    def setUp(self):
        """Create a test directory structure with known depth."""
        self.test_dir = tempfile.mkdtemp(prefix="test_early_term_")
        self.base_path = Path(self.test_dir)
        
        # Create a directory tree that goes to depth 4
        # depth 0: base
        # depth 1: 2 folders
        # depth 2: 2 folders  
        # depth 3: 1 folder
        # depth 4: 1 folder
        # depth 5+: none
        
        d1_a = self.base_path / "level1_a"
        d1_b = self.base_path / "level1_b"
        d1_a.mkdir()
        d1_b.mkdir()
        
        d2_a = d1_a / "level2_a"
        d2_b = d1_b / "level2_b"
        d2_a.mkdir()
        d2_b.mkdir()
        
        d3 = d2_a / "level3"
        d3.mkdir()
        
        d4 = d3 / "level4"
        d4.mkdir()
        
        # Add a file at depth 4 to ensure it's counted
        (d4 / "test.txt").write_text("test")
        
    def tearDown(self):
        """Clean up test directory."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_early_termination_stops_at_empty_depths(self):
        """Test that scanning stops after finding consecutive empty depths."""
        scanner = FolderScanner(skip_generated=True, verbose=2)
        
        # Request depths 0-100 (like --fix-all does)
        depths = list(range(0, 101))
        
        # Mock the print function to capture output
        with patch('builtins.print') as mock_print:
            results = scanner.scan_and_collect(
                self.base_path, 
                depths, 
                strategy='shallow',
                use_max_depth_detection=False  # Test early termination, not max depth detection
            )
        
        # Check that early termination message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        found_early_stop = any(
            "Stopping scan early" in str(call) 
            for call in print_calls
        )
        self.assertTrue(found_early_stop, "Early termination message not found")
        
        # Verify we didn't scan all 101 depths
        scanning_messages = [
            call for call in print_calls 
            if "Scanning at depth" in str(call)
        ]
        # Should stop around depth 6 or 7 (after finding 0 at depths 5 and 6)
        self.assertLess(len(scanning_messages), 10, 
                       f"Scanned too many depths: {len(scanning_messages)}")
        self.assertGreater(len(scanning_messages), 4,
                          f"Stopped too early: {len(scanning_messages)}")
        
    def test_early_termination_finds_all_folders(self):
        """Test that early termination doesn't miss any folders."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        
        # Request depths 0-100
        depths = list(range(0, 101))
        
        results = scanner.scan_and_collect(
            self.base_path,
            depths,
            strategy='shallow'
        )
        
        # Count folders returned
        folder_paths = [r[0] for r in results]
        
        # Should find exactly 7 folders (base + 6 subdirs)
        self.assertEqual(len(folder_paths), 7,
                        f"Expected 7 folders, found {len(folder_paths)}")
        
        # Verify all expected folders are found
        expected_names = [
            "",  # base
            "level1_a",
            "level1_b", 
            "level2_a",
            "level2_b",
            "level3",
            "level4"
        ]
        
        for expected in expected_names:
            found = any(
                str(folder).endswith(expected) if expected else True
                for folder in folder_paths
            )
            self.assertTrue(found, f"Missing folder: {expected}")
    
    def test_early_termination_with_gap(self):
        """Test that early termination allows one gap in folder structure."""
        # Create a structure with a gap (no folders at depth 2)
        gap_dir = tempfile.mkdtemp(prefix="test_gap_")
        try:
            base = Path(gap_dir)
            
            # depth 1: folder
            d1 = base / "level1"
            d1.mkdir()
            
            # depth 2: skip (gap)
            # depth 3: folder (unusual but possible)
            d3 = d1 / "skip" / "level3"
            d3.mkdir(parents=True)
            
            scanner = FolderScanner(skip_generated=True, verbose=0)
            depths = list(range(0, 10))
            
            results = scanner.scan_and_collect(base, depths, strategy='shallow')
            folder_paths = [r[0] for r in results]
            
            # Should find all folders despite gap
            self.assertEqual(len(folder_paths), 4)  # base, level1, skip, level3
            
        finally:
            if Path(gap_dir).exists():
                shutil.rmtree(gap_dir)
    
    def test_no_early_termination_when_disabled(self):
        """Test that we can disable early termination if needed."""
        scanner = FolderScanner(skip_generated=True, verbose=0)
        
        # For now, early termination is always on
        # This test documents current behavior
        # If we add a flag to disable it, update this test
        
        depths = list(range(0, 10))
        results = scanner.scan_and_collect(
            self.base_path,
            depths, 
            strategy='shallow'
        )
        
        # Should still find all folders
        self.assertEqual(len(results), 7)


if __name__ == '__main__':
    unittest.main()