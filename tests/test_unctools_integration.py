#!/usr/bin/env python3
"""
UNCtools integration tests - tests that require UNCtools to be available.

These tests verify that when UNCtools is available, we get enhanced functionality
beyond the basic path handling fallbacks.
"""

import sys
import os
import subprocess
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import unctools
    UNCTOOLS_AVAILABLE = True
except ImportError:
    UNCTOOLS_AVAILABLE = False

# Skip all tests in this module if UNCtools is not available
pytestmark = pytest.mark.skipif(
    not UNCTOOLS_AVAILABLE, 
    reason="UNCtools not available - these tests require UNCtools to be installed"
)


def run_cli(*args, cwd: Path = None) -> Dict[str, Any]:
    """
    Run the CLI with given arguments.
    
    Returns:
        Dict with 'returncode', 'stdout', 'stderr', 'success' keys
    """
    cmd = [sys.executable, '-m', 'folder_datetime_fix'] + list(args)
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    return {
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'success': result.returncode == 0,
        'cmd': cmd
    }


class TestUNCToolsDetection:
    """Test that UNCtools is properly detected and used."""
    
    def test_unctools_import_works(self):
        """Verify UNCtools can be imported and has expected functions."""
        import unctools
        
        # Check that key functions are available.
        # NOTE: `normalize_path` was removed in unctools 0.2.0 (probe-not-mutate);
        # the handler now normalizes via dazzle-filekit, so it is no longer
        # expected here. `get_path_type` -> `classify_path_origin` (renamed in 0.2.0).
        expected_functions = [
            'convert_to_local',
            'convert_to_unc',
            'is_unc_path',
            'is_network_drive',
            'is_subst_drive',
            'classify_path_origin',
            'get_network_mappings'
        ]
        
        for func_name in expected_functions:
            assert hasattr(unctools, func_name), f"UNCtools missing expected function: {func_name}"
    
    def test_unctools_detected_in_cli(self):
        """Test that CLI detects and reports UNCtools availability."""
        # Use a non-existent path so we can test detection without needing real network share
        result = run_cli('--unc-path', '\\\\nonexistent\\test', '--dry-run', '-v')
        
        # Should show UNCtools availability message
        assert 'UNCtools is available for enhanced network path support' in result['stdout'], \
               f"Expected UNCtools detection message in output: {result['stdout']}"
        
        # Should NOT show the fallback message
        assert 'UNCtools not found - using basic path handling' not in result['stdout'], \
               f"Unexpected fallback message when UNCtools should be available: {result['stdout']}"
    
    def test_unc_handler_detects_unctools(self):
        """Test UNCHandler directly detects UNCtools."""
        from folder_datetime_fix.unc_handler import get_unc_handler
        
        handler = get_unc_handler(verbose=False)
        assert handler.unctools_available, "UNCHandler should detect UNCtools as available"
        
        # Test with verbose to check message
        import io
        import contextlib
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            handler_verbose = get_unc_handler(verbose=True)
        
        output_text = output.getvalue()
        assert "UNCtools is available" in output_text, \
               f"Expected verbose UNCtools message, got: {output_text}"


class TestUNCToolsEnhancedFunctionality:
    """Test enhanced functionality that's only available with UNCtools."""
    
    def test_path_type_detection(self):
        """Test that UNCtools provides enhanced path type detection."""
        from folder_datetime_fix.unc_handler import get_unc_handler
        
        handler = get_unc_handler()
        
        # Test UNC path detection
        unc_path = "\\\\server\\share\\folder"
        path_info = handler.get_path_info(unc_path)
        
        assert 'type' in path_info, "Path info should include type when UNCtools available"
        assert path_info['is_unc'] is True, "UNC path should be detected as UNC"
        
        # Test local path
        local_path = "C:\\temp"
        path_info = handler.get_path_info(local_path)
        assert path_info['is_unc'] is False, "Local path should not be detected as UNC"
    
    def test_network_mappings_available(self):
        """Test that network mappings function is available."""
        from folder_datetime_fix.unc_handler import get_unc_handler
        
        handler = get_unc_handler()
        mappings = handler.get_network_mappings()
        
        # Should return a dict (even if empty)
        assert isinstance(mappings, dict), "Network mappings should return a dictionary"
    
    def test_path_conversion_functionality(self):
        """Test UNC path conversion capabilities."""
        from folder_datetime_fix.unc_handler import get_unc_handler
        
        handler = get_unc_handler()
        
        # Test path normalization with UNC path
        test_path = "\\\\server\\share"
        normalized, is_network = handler.convert_for_processing(test_path)
        
        assert isinstance(normalized, Path), "Should return Path object"
        assert isinstance(is_network, bool), "Should return boolean for network status"


class TestUNCToolsCLIIntegration:
    """Test CLI behavior specifically when UNCtools is available."""
    
    def test_cli_shows_unctools_enabled(self):
        """Test that CLI shows UNCtools status in header when available."""
        # Use current directory so path exists and we get full header
        result = run_cli('.', '--dry-run', '-v')
        
        # Should show UNCtools detection message
        assert 'UNCtools is available for enhanced network path support' in result['stdout'], \
               f"Expected UNCtools detection message: {result['stdout']}"
    
    def test_cli_unc_path_processing(self):
        """Test that CLI processes UNC paths with enhanced functionality."""
        # Test with a UNC path that should show enhanced processing
        # Even if path doesn't exist, it should show the UNC detection before failing
        result = run_cli('--unc-path', '\\\\server\\share', '--dry-run', '-v')
        
        # Should show UNCtools processing (even if path doesn't exist)
        assert 'UNCtools is available for enhanced network path support' in result['stdout'] or \
               'Converted UNC to local:' in result['stdout'], \
               f"Expected UNC processing with UNCtools: {result['stdout']}"
    
    def test_verbose_shows_unctools_operations(self):
        """Test that verbose mode shows UNCtools-specific operations."""
        result = run_cli('--unc-path', '\\\\server\\share', '--dry-run', '-vv')
        
        # Look for UNCtools-specific verbose messages
        stdout = result['stdout']
        
        # Should show some UNCtools operations (path conversion, etc.)
        has_unctools_ops = any(phrase in stdout for phrase in [
            'Converted UNC to local',
            'UNCtools',
            'network path',
        ])
        
        assert has_unctools_ops, f"Expected UNCtools operations in verbose output: {stdout}"


class TestUNCToolsErrorHandling:
    """Test error handling behavior when UNCtools is available."""
    
    def test_network_error_handling_enhanced(self):
        """Test that network errors are handled with UNCtools context."""
        from folder_datetime_fix.unc_handler import get_unc_handler
        
        handler = get_unc_handler()
        
        # Test error handling (this method should exist and handle network errors)
        mock_error = OSError("Network path not found")
        mock_path = Path("\\\\nonexistent\\server")
        
        # Should not crash and should return boolean indicating handling
        handled = handler.handle_network_error(mock_error, mock_path)
        assert isinstance(handled, bool), "Error handler should return boolean"


def test_unctools_requirement():
    """Meta-test: Verify that this test module correctly requires UNCtools."""
    # If we get here, UNCtools was successfully imported
    assert UNCTOOLS_AVAILABLE, "This test module should only run when UNCtools is available"
    
    # Verify we can actually use UNCtools functions
    from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE as handler_available
    assert handler_available, "UNC handler should also detect UNCtools as available"


if __name__ == '__main__':
    # Run tests directly if called as script
    pytest.main([__file__])