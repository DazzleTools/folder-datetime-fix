"""Tests for analysis strategy implementations."""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from folder_datetime_fix.folder_scanner_dazzle import FolderScanner
from folder_datetime_fix.analysis_strategies_dazzle import (
    AnalysisStrategy,
    StandardStrategy,
    LowMemoryStrategy,
    TreeStrategy,
    AutoStrategy,
    StrategyFactory
)


class TestAnalysisStrategies(unittest.TestCase):
    """Test cases for analysis strategy implementations."""
    
    def setUp(self):
        """Create test directory structure."""
        self.test_dir = tempfile.mkdtemp(prefix='test_strategies_')
        self.scanner = FolderScanner(skip_generated=True, verbose=0)
        
        # Create test structure
        self.create_test_structure()
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_structure(self):
        """Create a sample directory structure for testing."""
        base = Path(self.test_dir)
        
        # Create folders at different depths
        (base / "folder1").mkdir()
        (base / "folder2").mkdir()
        (base / "folder1" / "subfolder1").mkdir()
        (base / "folder1" / "subfolder2").mkdir()
        (base / "folder2" / "deep" / "nested").mkdir(parents=True)
        
        # Create some files
        (base / "file1.txt").touch()
        (base / "folder1" / "file2.txt").touch()
        (base / "folder1" / "subfolder1" / "file3.txt").touch()
        (base / "folder2" / "deep" / "nested" / "file4.txt").touch()
    
    def test_standard_strategy_shallow(self):
        """Test StandardStrategy with shallow scanning."""
        strategy = StandardStrategy(self.scanner, 'shallow')
        self.assertEqual(strategy.get_name(), 'standard-shallow')
        
        results = strategy.analyze(Path(self.test_dir), [0, 1])
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        
        # Check that results are tuples of (Path, Optional[datetime])
        for folder, timestamp in results:
            self.assertIsInstance(folder, Path)
            self.assertTrue(timestamp is None or isinstance(timestamp, datetime))
    
    def test_standard_strategy_deep(self):
        """Test StandardStrategy with deep scanning."""
        strategy = StandardStrategy(self.scanner, 'deep')
        self.assertEqual(strategy.get_name(), 'standard-deep')
        
        results = strategy.analyze(Path(self.test_dir), [0])
        self.assertIsInstance(results, list)
        
        # Deep strategy should process all subfolders
        folder_paths = [folder for folder, _ in results]
        self.assertTrue(any('deep' in str(p) for p in folder_paths))
        self.assertTrue(any('nested' in str(p) for p in folder_paths))
    
    def test_standard_strategy_smart(self):
        """Test StandardStrategy with smart scanning."""
        strategy = StandardStrategy(self.scanner, 'smart')
        self.assertEqual(strategy.get_name(), 'standard-smart')
        
        results = strategy.analyze(Path(self.test_dir), [0, 1])
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
    
    def test_low_memory_strategy(self):
        """Test LowMemoryStrategy disables caching."""
        # Create scanner with caching enabled
        scanner_with_cache = FolderScanner(skip_generated=True, verbose=0, use_cache=True)
        self.assertIsNotNone(scanner_with_cache.cache)
        
        # LowMemoryStrategy should disable cache
        strategy = LowMemoryStrategy(scanner_with_cache, 'shallow')
        self.assertEqual(strategy.get_name(), 'low-memory-shallow')
        self.assertFalse(strategy.scanner.use_cache)
        self.assertIsNone(strategy.scanner.cache)
        
        results = strategy.analyze(Path(self.test_dir), [0, 1])
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
    
    def test_tree_strategy(self):
        """Test TreeStrategy with bottom-up computation."""
        strategy = TreeStrategy(self.scanner)
        self.assertEqual(strategy.get_name(), 'tree')
        self.assertIn('tree', strategy.get_description().lower())
        self.assertIn('bottom-up', strategy.get_description().lower())
        
        # Should work with tree structure
        results = strategy.analyze(Path(self.test_dir), [0])
        self.assertIsInstance(results, list)
        # Tree mode computes timestamps
        self.assertTrue(len(results) > 0)
    
    def test_folder_only_strategy(self):
        """Test FolderOnlyStrategy (ultra-minimal mode)."""
        from folder_datetime_fix.analysis_strategies_dazzle import FolderOnlyStrategy
        strategy = FolderOnlyStrategy(self.scanner)
        self.assertEqual(strategy.get_name(), 'folder-only')
        self.assertIn('minimal', strategy.get_description().lower())
        
        # Should work computing timestamps without storing files
        results = strategy.analyze(Path(self.test_dir), [0])
        self.assertIsInstance(results, list)
        # Folders with files should have computed timestamps
        # Empty folders might have None
        self.assertTrue(len(results) > 0)
    
    def test_auto_strategy_local(self):
        """Test AutoStrategy on local path."""
        strategy = AutoStrategy(self.scanner)
        self.assertEqual(strategy.get_name(), 'auto')
        
        results = strategy.analyze(Path(self.test_dir), [0, 1])
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        
        # Should select a strategy
        self.assertIsNotNone(strategy.selected_strategy)
        self.assertIn('auto(', strategy.get_name())
    
    def test_auto_strategy_network_detection(self):
        """Test AutoStrategy detects network paths."""
        # Create a mock network path (starts with \\)
        # Note: We can't actually test network paths in unit tests
        # but we can test the detection logic
        strategy = AutoStrategy(self.scanner)
        
        # Test with regular path (should select standard)
        results = strategy.analyze(Path(self.test_dir), [0])
        self.assertIsNotNone(strategy.selected_strategy)
        # For small local trees, should use standard
        self.assertIsInstance(strategy.selected_strategy, (StandardStrategy, LowMemoryStrategy))
    
    def test_strategy_factory_create(self):
        """Test StrategyFactory creates correct strategies."""
        # Test standard strategy creation
        strategy = StrategyFactory.create_strategy('standard', self.scanner, 'shallow')
        self.assertIsInstance(strategy, StandardStrategy)
        
        # Test low-memory strategy creation
        strategy = StrategyFactory.create_strategy('low-memory', self.scanner, 'deep')
        self.assertIsInstance(strategy, LowMemoryStrategy)
        
        # Test tree strategy creation
        strategy = StrategyFactory.create_strategy('tree', self.scanner)
        self.assertIsInstance(strategy, TreeStrategy)
        
        # Test auto strategy creation
        strategy = StrategyFactory.create_strategy('auto', self.scanner)
        self.assertIsInstance(strategy, AutoStrategy)
        
        # Test default (should be standard)
        strategy = StrategyFactory.create_strategy('unknown', self.scanner)
        self.assertIsInstance(strategy, StandardStrategy)
    
    def test_strategy_factory_modifiers(self):
        """Test StrategyFactory handles modifiers."""
        # Test no-cache modifier
        scanner_with_cache = FolderScanner(skip_generated=True, verbose=0, use_cache=True)
        strategy = StrategyFactory.create_strategy('standard,no-cache', scanner_with_cache, 'shallow')
        self.assertFalse(strategy.scanner.use_cache)
        
        # Test low-memory modifier
        strategy = StrategyFactory.create_strategy('auto,low-memory', self.scanner)
        self.assertIsInstance(strategy, LowMemoryStrategy)
    
    def test_strategy_config(self):
        """Test strategy configuration retrieval."""
        strategy = StandardStrategy(self.scanner, 'deep')
        config = strategy.get_config()
        
        self.assertEqual(config['name'], 'standard-deep')
        self.assertIn('description', config)
        self.assertIn('cache_enabled', config)
        self.assertIn('skip_generated', config)
    
    def test_available_strategies(self):
        """Test listing available strategies."""
        strategies = StrategyFactory.get_available_strategies()
        
        self.assertIn('auto', strategies)
        self.assertIn('standard', strategies)
        self.assertIn('low-memory', strategies)
        self.assertIn('tree', strategies)
        self.assertIn('folder-only', strategies)
        self.assertEqual(len(strategies), 5)
    
    def test_strategy_with_empty_folders(self):
        """Test strategies handle empty folders correctly."""
        # Create an empty folder
        empty_dir = Path(self.test_dir) / "empty_folder"
        empty_dir.mkdir()
        
        strategy = StandardStrategy(self.scanner, 'shallow')
        results = strategy.analyze(Path(self.test_dir), [1])
        
        # Should handle empty folders without errors
        folder_paths = [str(folder) for folder, _ in results]
        self.assertIn(str(empty_dir), folder_paths)
        
        # Empty folder should have None timestamp
        for folder, timestamp in results:
            if folder == empty_dir:
                self.assertIsNone(timestamp)
    
    def test_strategy_with_system_files(self):
        """Test strategies skip system files correctly."""
        # Create a folder with system files
        sys_dir = Path(self.test_dir) / "with_system"
        sys_dir.mkdir()
        (sys_dir / "thumbs.db").touch()
        (sys_dir / "desktop.ini").touch()
        (sys_dir / "real_file.txt").touch()
        
        # Scanner should skip system files
        strategy = StandardStrategy(self.scanner, 'shallow')
        results = strategy.analyze(sys_dir, [0])
        
        # Should process the folder
        self.assertEqual(len(results), 1)
        folder, timestamp = results[0]
        self.assertEqual(folder, sys_dir)
        # Should have timestamp from real_file.txt, not system files
        self.assertIsNotNone(timestamp)


if __name__ == '__main__':
    unittest.main()