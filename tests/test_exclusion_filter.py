"""
Test suite for ExclusionFilter with glob pattern support.
"""

import unittest
from pathlib import Path
from folder_datetime_fix.exclusion_filter import ExclusionFilter, ExclusionMode


class TestExclusionModes(unittest.TestCase):
    """Test basic exclusion modes."""
    
    def test_default_mode(self):
        """Test default mode excludes system files and folders."""
        filter = ExclusionFilter(ExclusionMode.DEFAULT)
        
        # Should exclude known system files
        self.assertTrue(filter.should_exclude(Path('thumbs.db'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('desktop.ini'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('.DS_Store'), is_dir=False))
        
        # Should exclude known system folders
        self.assertTrue(filter.should_exclude(Path('__pycache__'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('.git'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('node_modules'), is_dir=True))
        
        # Should not exclude regular files and folders
        self.assertFalse(filter.should_exclude(Path('myfile.txt'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('myproject'), is_dir=True))
    
    def test_none_mode(self):
        """Test none mode includes everything."""
        filter = ExclusionFilter(ExclusionMode.NONE)
        
        # Should include system files
        self.assertFalse(filter.should_exclude(Path('thumbs.db'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('__pycache__'), is_dir=True))
        
        # Should include regular files
        self.assertFalse(filter.should_exclude(Path('myfile.txt'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('myproject'), is_dir=True))
    
    def test_files_mode(self):
        """Test files mode excludes only system files."""
        filter = ExclusionFilter(ExclusionMode.FILES)
        
        # Should exclude system files
        self.assertTrue(filter.should_exclude(Path('thumbs.db'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('desktop.ini'), is_dir=False))
        
        # Should NOT exclude system folders
        self.assertFalse(filter.should_exclude(Path('__pycache__'), is_dir=True))
        self.assertFalse(filter.should_exclude(Path('.git'), is_dir=True))
        
        # Should not exclude regular files
        self.assertFalse(filter.should_exclude(Path('myfile.txt'), is_dir=False))
    
    def test_folders_mode(self):
        """Test folders mode excludes only system folders."""
        filter = ExclusionFilter(ExclusionMode.FOLDERS)
        
        # Should NOT exclude system files
        self.assertFalse(filter.should_exclude(Path('thumbs.db'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('desktop.ini'), is_dir=False))
        
        # Should exclude system folders
        self.assertTrue(filter.should_exclude(Path('__pycache__'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('.git'), is_dir=True))
        
        # Should not exclude regular folders
        self.assertFalse(filter.should_exclude(Path('myproject'), is_dir=True))


class TestSmartDetection(unittest.TestCase):
    """Test smart file/folder detection."""
    
    def test_smart_folder_detection(self):
        """Test that known folder names are treated as folders."""
        filter = ExclusionFilter(
            exclude_patterns=['.vscode', '__pycache__']
        )
        
        # Should detect these as folders even without is_dir specified
        self.assertTrue(filter.should_exclude(Path('.vscode')))
        self.assertTrue(filter.should_exclude(Path('__pycache__')))
    
    def test_smart_file_detection(self):
        """Test that known file names are treated as files."""
        filter = ExclusionFilter(
            exclude_patterns=['thumbs.db', 'desktop.ini']
        )
        
        # Should detect these as files even without is_dir specified
        self.assertTrue(filter.should_exclude(Path('thumbs.db')))
        self.assertTrue(filter.should_exclude(Path('desktop.ini')))
    
    def test_extension_detection(self):
        """Test that files with extensions are detected as files."""
        filter = ExclusionFilter(
            exclude_patterns=['*.tmp', '*.bak']
        )
        
        # Should detect these as files based on extension
        self.assertTrue(filter.should_exclude(Path('file.tmp')))
        self.assertTrue(filter.should_exclude(Path('backup.bak')))


class TestSimplePatterns(unittest.TestCase):
    """Test simple glob patterns."""
    
    def test_wildcard_patterns(self):
        """Test * wildcard matching."""
        filter = ExclusionFilter(
            exclude_patterns=['*.tmp', 'test_*', '*_backup']
        )
        
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('test_file.txt'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('data_backup'), is_dir=False))
        
        self.assertFalse(filter.should_exclude(Path('file.txt'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('production.py'), is_dir=False))
    
    def test_question_mark_pattern(self):
        """Test ? single character matching."""
        filter = ExclusionFilter(
            mode=ExclusionMode.NONE,  # Disable mode-based filtering to test patterns only
            exclude_patterns=['temp?.txt', '??.tmp']
        )
        
        self.assertTrue(filter.should_exclude(Path('temp1.txt'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('temp2.txt'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('ab.tmp'), is_dir=False))
        
        self.assertFalse(filter.should_exclude(Path('temp10.txt'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('a.tmp'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('abc.tmp'), is_dir=False))
    
    def test_directory_marker_patterns(self):
        """Test patterns ending with / for directories."""
        filter = ExclusionFilter(
            exclude_patterns=['build/', 'dist/', 'temp/']
        )
        
        # Should match directories
        self.assertTrue(filter.should_exclude(Path('build'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('dist'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('temp'), is_dir=True))
        
        # Should NOT match files with same name
        self.assertFalse(filter.should_exclude(Path('build'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('dist'), is_dir=False))


class TestRecursivePatterns(unittest.TestCase):
    """Test ** recursive patterns."""
    
    def test_recursive_directory_pattern(self):
        """Test **/dir pattern matches at any depth."""
        filter = ExclusionFilter(
            exclude_patterns=['**/node_modules', '**/build']
        )
        
        # Should match at any depth
        self.assertTrue(filter.should_exclude(Path('node_modules'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('project/node_modules'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('deep/path/node_modules'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('src/build'), is_dir=True))
        
        # Should not match other directories
        self.assertFalse(filter.should_exclude(Path('src'), is_dir=True))
        self.assertFalse(filter.should_exclude(Path('modules'), is_dir=True))
    
    def test_recursive_file_pattern(self):
        """Test **/*.ext pattern matches files at any depth."""
        filter = ExclusionFilter(
            exclude_patterns=['**/*.tmp', '**/*.cache']
        )
        
        # Should match at any depth
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('dir/file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('deep/path/to/file.cache'), is_dir=False))
        
        # Should not match other files
        self.assertFalse(filter.should_exclude(Path('file.txt'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('dir/file.py'), is_dir=False))
    
    def test_recursive_with_prefix(self):
        """Test patterns like test/**/*.py."""
        filter = ExclusionFilter(
            mode=ExclusionMode.NONE,  # Disable mode filtering to test patterns only
            exclude_patterns=['test/**/*.tmp', 'src/**/backup/*']
        )
        
        # Should match specific paths
        self.assertTrue(filter.should_exclude(Path('test/unit/file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('test/integration/deep/file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('src/module/backup/file.txt'), is_dir=False))
        
        # Should not match outside prefix
        self.assertFalse(filter.should_exclude(Path('production/file.tmp'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('backup/file.txt'), is_dir=False))


class TestIncludeOverrides(unittest.TestCase):
    """Test that include patterns override excludes."""
    
    def test_simple_override(self):
        """Test simple include overrides exclude."""
        filter = ExclusionFilter(
            exclude_patterns=['*.log'],
            include_patterns=['important.log']
        )
        
        # Include pattern should override
        self.assertFalse(filter.should_exclude(Path('important.log'), is_dir=False))
        
        # Other logs should still be excluded
        self.assertTrue(filter.should_exclude(Path('debug.log'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('error.log'), is_dir=False))
    
    def test_pattern_override(self):
        """Test pattern includes override pattern excludes."""
        filter = ExclusionFilter(
            exclude_patterns=['*.tmp', 'temp/*'],
            include_patterns=['*.config.tmp', 'temp/keep/*']
        )
        
        # Specific patterns should override
        self.assertFalse(filter.should_exclude(Path('app.config.tmp'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('temp/keep/file.txt'), is_dir=False))
        
        # General patterns should still exclude
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('temp/delete.txt'), is_dir=False))
    
    def test_mode_with_includes(self):
        """Test that includes override mode-based exclusions."""
        filter = ExclusionFilter(
            mode=ExclusionMode.DEFAULT,
            include_patterns=['.vscode/settings.json', '.git/config']
        )
        
        # Includes should override system exclusion
        self.assertFalse(filter.should_exclude(Path('.vscode/settings.json'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('.git/config'), is_dir=False))
        
        # But other system files should still be excluded
        self.assertTrue(filter.should_exclude(Path('thumbs.db'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('__pycache__'), is_dir=True))


class TestComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""
    
    def test_mixed_patterns(self):
        """Test combination of different pattern types."""
        filter = ExclusionFilter(
            mode=ExclusionMode.DEFAULT,
            exclude_patterns=['*.tmp', '*.bak', 'build/', '**/cache', 'logs/**'],
            include_patterns=['.vscode/', 'build/important.txt', '*.config.bak']
        )
        
        # Test various scenarios
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('backup.bak'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('app.config.bak'), is_dir=False))  # Included
        
        self.assertTrue(filter.should_exclude(Path('build'), is_dir=True))
        self.assertFalse(filter.should_exclude(Path('build/important.txt'), is_dir=False))  # Included
        
        self.assertFalse(filter.should_exclude(Path('.vscode'), is_dir=True))  # Included
        self.assertTrue(filter.should_exclude(Path('.git'), is_dir=True))  # System default
        
        self.assertTrue(filter.should_exclude(Path('dir/cache'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('logs/error.log'), is_dir=False))
    
    def test_case_insensitivity(self):
        """Test that patterns are case-insensitive."""
        filter = ExclusionFilter(
            exclude_patterns=['*.TMP', 'BUILD/'],
            include_patterns=['IMPORTANT.tmp']
        )
        
        # Should match regardless of case
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('FILE.TMP'), is_dir=False))
        self.assertTrue(filter.should_exclude(Path('build'), is_dir=True))
        self.assertTrue(filter.should_exclude(Path('BUILD'), is_dir=True))
        
        # Include should also be case-insensitive
        self.assertFalse(filter.should_exclude(Path('important.tmp'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('IMPORTANT.TMP'), is_dir=False))


class TestFromArgs(unittest.TestCase):
    """Test creating filters from CLI arguments."""
    
    def test_from_args_basic(self):
        """Test basic argument parsing."""
        filter = ExclusionFilter.from_args(
            mode='files',
            exclude='*.tmp,*.bak',
            include='.vscode/settings.json'
        )
        
        self.assertEqual(filter.mode, ExclusionMode.FILES)
        self.assertEqual(len(filter.exclude_patterns), 2)
        self.assertEqual(len(filter.include_patterns), 1)
        
        # Test functionality
        self.assertTrue(filter.should_exclude(Path('file.tmp'), is_dir=False))
        self.assertFalse(filter.should_exclude(Path('.vscode/settings.json'), is_dir=False))
    
    def test_from_args_empty(self):
        """Test with no patterns."""
        filter = ExclusionFilter.from_args(mode='default')
        
        self.assertEqual(filter.mode, ExclusionMode.DEFAULT)
        self.assertEqual(len(filter.exclude_patterns), 0)
        self.assertEqual(len(filter.include_patterns), 0)
    
    def test_from_args_complex(self):
        """Test complex pattern parsing."""
        filter = ExclusionFilter.from_args(
            mode='none',
            exclude='*.tmp, build/, **/*.cache, test_* ',
            include=' .git/config, *.important '
        )
        
        # Should handle whitespace
        self.assertEqual(len(filter.exclude_patterns), 4)
        self.assertEqual(len(filter.include_patterns), 2)
        self.assertIn('*.tmp', filter.exclude_patterns)
        self.assertIn('.git/config', filter.include_patterns)
    
    def test_from_legacy(self):
        """Test legacy skip_generated conversion."""
        # skip_generated=True -> DEFAULT mode
        filter1 = ExclusionFilter.from_legacy(skip_generated=True)
        self.assertEqual(filter1.mode, ExclusionMode.DEFAULT)
        self.assertTrue(filter1.should_exclude(Path('thumbs.db'), is_dir=False))
        
        # skip_generated=False -> NONE mode
        filter2 = ExclusionFilter.from_legacy(skip_generated=False)
        self.assertEqual(filter2.mode, ExclusionMode.NONE)
        self.assertFalse(filter2.should_exclude(Path('thumbs.db'), is_dir=False))


if __name__ == '__main__':
    unittest.main()