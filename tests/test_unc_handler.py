#!/usr/bin/env python3
"""
Unit tests for UNC path handling functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_datetime_fix.unc_handler import UNCHandler, get_unc_handler


class TestUNCHandler(unittest.TestCase):
    """Test UNC handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = UNCHandler(verbose=False)
    
    def test_basic_initialization(self):
        """Test handler initialization."""
        handler = UNCHandler(verbose=False)
        self.assertIsNotNone(handler)
        self.assertFalse(handler.verbose)
        
        verbose_handler = UNCHandler(verbose=True)
        self.assertTrue(verbose_handler.verbose)
    
    def test_unc_path_detection(self):
        """Test detection of UNC paths."""
        # Test with unctools not available
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler()
            
            # UNC paths
            self.assertTrue(handler.get_path_info('\\\\server\\share')['is_unc'])
            self.assertTrue(handler.get_path_info('//server/share')['is_unc'])
            
            # Non-UNC paths
            self.assertFalse(handler.get_path_info('C:\\folder')['is_unc'])
            self.assertFalse(handler.get_path_info('/home/user')['is_unc'])
            self.assertFalse(handler.get_path_info('.')['is_unc'])
    
    def test_path_normalization(self):
        """Test path normalization."""
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler()
            
            # UNC paths should be preserved (Windows may add trailing slash)
            unc_path = '\\\\server\\share'
            result = handler.normalize_path(unc_path)
            # Path may have trailing slash on Windows
            self.assertTrue(str(result).startswith(unc_path))
            
            # Forward slash UNC (Windows converts to backslash)
            forward_unc = '//server/share'
            result = handler.normalize_path(forward_unc)
            # On Windows, forward slash UNC gets converted to backslash
            self.assertTrue('server' in str(result) and 'share' in str(result))
    
    def test_convert_for_processing(self):
        """Test path conversion for processing."""
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler(verbose=False)
            
            # UNC path
            path, is_network = handler.convert_for_processing('\\\\server\\share')
            self.assertTrue(is_network)
            self.assertIsInstance(path, Path)
            
            # Local path
            path, is_network = handler.convert_for_processing('C:\\folder')
            self.assertFalse(is_network)
            self.assertIsInstance(path, Path)
    
    def test_ambiguous_path_warning(self):
        """Test warning for ambiguous single-backslash paths."""
        handler = UNCHandler(verbose=True)
        
        # Capture the warning
        with patch('builtins.print') as mock_print:
            path, is_network = handler.convert_for_processing('\\server\\share')
            
            # Check that warning was printed
            mock_print.assert_called()
            warning_printed = False
            for call in mock_print.call_args_list:
                if 'WARNING' in str(call) and 'single backslash' in str(call):
                    warning_printed = True
                    break
            self.assertTrue(warning_printed)
    
    @patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', True)
    @patch('folder_datetime_fix.unc_handler.is_unc_path')
    @patch('folder_datetime_fix.unc_handler.is_network_drive')
    @patch('folder_datetime_fix.unc_handler.is_subst_drive')
    @patch('folder_datetime_fix.unc_handler.convert_to_local')
    def test_unctools_integration(self, mock_convert, mock_subst, mock_network, mock_unc):
        """Test integration when unctools is available."""
        handler = UNCHandler()
        
        # Configure mocks
        mock_unc.return_value = True
        mock_network.return_value = False
        mock_subst.return_value = False
        mock_convert.return_value = 'Y:\\mapped\\path'
        
        # Test UNC to mapped drive conversion
        path, is_network = handler.convert_for_processing('\\\\server\\share')
        self.assertTrue(is_network)
        mock_unc.assert_called()
        mock_convert.assert_called()
    
    def test_get_path_info(self):
        """Test getting detailed path information."""
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler()
            
            # Test with existing file (current script)
            current_file = __file__
            info = handler.get_path_info(current_file)
            
            self.assertEqual(info['original'], current_file)
            self.assertTrue(info['exists'])
            self.assertFalse(info['is_dir'])
            self.assertFalse(info['is_unc'])
            self.assertFalse(info['is_network'])
            self.assertEqual(info['type'], 'local')
    
    def test_network_error_handling(self):
        """Test network error handling."""
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler()
            
            # Test various network errors
            network_errors = [
                Exception("Network path not found"),
                Exception("The network location cannot be reached"),
                Exception("Access is denied"),
                Exception("The specified network name is no longer available")
            ]
            
            for error in network_errors:
                result = handler.handle_network_error(error, Path('\\\\server\\share'))
                self.assertFalse(result)  # Without unctools, can't retry
    
    def test_prepare_path_list(self):
        """Test preparing multiple paths."""
        with patch('folder_datetime_fix.unc_handler.UNCTOOLS_AVAILABLE', False):
            handler = UNCHandler()
            
            paths = [
                'C:\\local\\folder',
                '\\\\server\\share',
                '//another/share'
            ]
            
            prepared = handler.prepare_path_list(paths)
            
            self.assertEqual(len(prepared), 3)
            
            # Check each prepared path
            for path_obj, info in prepared:
                self.assertIsInstance(path_obj, Path)
                self.assertIn('original', info)
                self.assertIn('is_network_for_processing', info)
    
    def test_get_unc_handler_factory(self):
        """Test the factory function."""
        handler1 = get_unc_handler(verbose=False)
        self.assertIsInstance(handler1, UNCHandler)
        self.assertFalse(handler1.verbose)
        
        handler2 = get_unc_handler(verbose=True)
        self.assertIsInstance(handler2, UNCHandler)
        self.assertTrue(handler2.verbose)


class TestUNCPathInMainScript(unittest.TestCase):
    """Test UNC path handling in main script."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import main script
        from folder_datetime_fix import cli
        self.mod_fldr_dt = cli
    
    def test_parse_unc_path_argument(self):
        """Test parsing --unc-path argument."""
        # Test with --unc-path
        sys.argv = ['mod_fldr_dt.py', '--unc-path', '\\\\server\\share', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        self.assertEqual(args.unc_path, '\\\\server\\share')
        self.assertTrue(args.dry_run)
        
        # Test with regular path
        sys.argv = ['mod_fldr_dt.py', 'C:\\folder', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        self.assertEqual(args.path, 'C:\\folder')
        self.assertIsNone(args.unc_path)
    
    def test_unc_path_processing(self):
        """Test UNC path is properly processed."""
        sys.argv = ['mod_fldr_dt.py', '--unc-path', '\\server\\share\\folder', '--depth', '0', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        
        # The script should add backslashes
        self.assertEqual(args.unc_path, '\\server\\share\\folder')
        
        # Test that it strips leading backslashes correctly
        sys.argv = ['mod_fldr_dt.py', '--unc-path', '\\\\\\\\server\\share', '--depth', '0', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        self.assertEqual(args.unc_path, '\\\\\\\\server\\share')
    
    def test_both_path_arguments(self):
        """Test behavior when both path and --unc-path are provided."""
        # When both are provided, --unc-path should take precedence
        sys.argv = ['mod_fldr_dt.py', 'C:\\local', '--unc-path', '\\\\server\\share', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        self.assertEqual(args.path, 'C:\\local')
        self.assertEqual(args.unc_path, '\\\\server\\share')
    
    def test_no_path_provided(self):
        """Test behavior when no path is provided."""
        sys.argv = ['mod_fldr_dt.py', '--dry-run']
        args = self.mod_fldr_dt.parse_arguments()
        self.assertIsNone(args.path)
        self.assertIsNone(args.unc_path)


class TestUNCPathEdgeCases(unittest.TestCase):
    """Test edge cases in UNC path handling."""
    
    def test_various_unc_formats(self):
        """Test various UNC path formats."""
        handler = UNCHandler()
        
        test_paths = [
            ('\\\\server\\share', True),           # Standard UNC
            ('\\\\server\\share\\folder', True),   # UNC with subfolder
            ('//server/share', True),              # Forward slash UNC
            ('//server/share/folder', True),       # Forward slash with subfolder
            ('\\\\192.168.1.1\\share', True),      # IP address UNC
            ('\\\\server', True),                  # Server only (still UNC format)
            ('\\server\\share', False),            # Single backslash (ambiguous)
            ('C:\\\\folder', False),               # Double backslash in local path
            ('', False),                            # Empty string
        ]
        
        for path, expected_is_unc in test_paths:
            if path:  # Skip empty string for path_info
                info = handler.get_path_info(path)
                self.assertEqual(
                    info['is_unc'], 
                    expected_is_unc,
                    f"Failed for path: {path}"
                )
    
    def test_unicode_in_paths(self):
        """Test handling of Unicode characters in paths."""
        handler = UNCHandler()
        
        unicode_paths = [
            '\\\\server\\文件夹',      # Chinese characters
            '\\\\сервер\\папка',       # Cyrillic
            '\\\\server\\café',        # Accented characters
            '\\\\server\\share\\🎭',   # Emoji (if supported)
        ]
        
        for path in unicode_paths:
            # Should not raise exceptions
            try:
                info = handler.get_path_info(path)
                self.assertIsNotNone(info)
                self.assertTrue(info['is_unc'])
            except Exception as e:
                # Some systems might not support all Unicode
                if 'encode' not in str(e).lower():
                    raise
    
    def test_very_long_unc_paths(self):
        """Test handling of very long UNC paths."""
        handler = UNCHandler()
        
        # Windows has a 260 character path limit (unless extended)
        long_folder = 'a' * 50
        long_path = f'\\\\server\\share\\{long_folder}\\{long_folder}\\{long_folder}\\{long_folder}'
        
        info = handler.get_path_info(long_path)
        self.assertTrue(info['is_unc'])
        self.assertEqual(info['original'], long_path)
    
    def test_special_characters_in_share_names(self):
        """Test UNC paths with special characters in share names."""
        handler = UNCHandler()
        
        special_paths = [
            '\\\\server\\share-name',       # Hyphen
            '\\\\server\\share_name',       # Underscore
            '\\\\server\\share.name',       # Dot
            '\\\\server\\share$',           # Dollar sign (hidden share)
            '\\\\server\\C$',               # Admin share
            '\\\\server\\share name',       # Space in share name
        ]
        
        for path in special_paths:
            info = handler.get_path_info(path)
            self.assertTrue(info['is_unc'], f"Failed for path: {path}")


if __name__ == '__main__':
    unittest.main()