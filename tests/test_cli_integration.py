#!/usr/bin/env python3
"""
Comprehensive CLI integration tests for folder_datetime_fix.

This test suite focuses on end-to-end CLI functionality to catch
API integration issues that unit tests might miss.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class CLITestResult:
    """Container for CLI test results."""
    def __init__(self, returncode: int, stdout: str, stderr: str, cmd: List[str]):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.cmd = cmd
        self.success = returncode == 0


def run_cli(*args, cwd: Path = None) -> CLITestResult:
    """
    Run the CLI with given arguments.
    
    Args:
        *args: Arguments to pass to the CLI
        cwd: Working directory to run from
        
    Returns:
        CLITestResult object
    """
    cmd = [sys.executable, '-m', 'folder_datetime_fix'] + list(args)
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    return CLITestResult(result.returncode, result.stdout, result.stderr, cmd)


def create_test_folder_structure(base_path: Path) -> Dict[str, Path]:
    """
    Create a simple test folder structure for CLI testing.
    
    Returns:
        Dict mapping folder names to Path objects
    """
    folders = {}
    
    # Create test folders
    folders['root'] = base_path
    folders['empty'] = base_path / 'empty_folder'
    folders['with_files'] = base_path / 'with_files' 
    folders['with_subfolders'] = base_path / 'with_subfolders'
    folders['subfolder'] = base_path / 'with_subfolders' / 'subfolder'
    
    # Create the directories
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    
    # Add some test files with known timestamps
    test_time = datetime(2024, 1, 15, 12, 0, 0)
    test_timestamp = test_time.timestamp()
    
    # Files in with_files folder
    test_file = folders['with_files'] / 'test.txt'
    test_file.write_text('test content')
    os.utime(test_file, (test_timestamp, test_timestamp))
    
    # Files in subfolder
    sub_file = folders['subfolder'] / 'sub.txt'
    sub_file.write_text('sub content')  
    os.utime(sub_file, (test_timestamp, test_timestamp))
    
    return folders


class TestCLIBasicFunctionality:
    """Test basic CLI functionality."""
    
    def setup_method(self):
        """Create temporary test directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.folders = create_test_folder_structure(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary test directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_help_displays_correctly(self):
        """Test that --help works and displays expected content."""
        result = run_cli('--help')
        assert result.success, f"Help command failed: {result.stderr}"
        assert 'Folder DateTime Fix Tool' in result.stdout or 'Fix folder modified timestamps' in result.stdout
        assert '--depth' in result.stdout
        assert '--strategy' in result.stdout
    
    def test_brief_help_works(self):
        """Test that -h works and displays brief help.""" 
        result = run_cli('-h')
        assert result.success, f"Brief help failed: {result.stderr}"
        assert 'usage:' in result.stdout
    
    def test_version_displays(self):
        """Test that --version works."""
        result = run_cli('--version')
        assert result.success, f"Version command failed: {result.stderr}"
        # Should contain version number
        assert any(char.isdigit() for char in result.stdout)
    
    def test_no_args_shows_minimal_help(self):
        """Test that no arguments shows minimal help and exits with error code."""
        result = run_cli()
        assert not result.success, "No args should fail with usage error"
        assert 'usage:' in result.stderr or 'usage:' in result.stdout


class TestCLIArgumentParsing:
    """Test CLI argument parsing and validation."""
    
    def setup_method(self):
        """Create temporary test directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.folders = create_test_folder_structure(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary test directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_dry_run(self):
        """Test basic dry run functionality."""
        result = run_cli(str(self.temp_dir), '--dry-run')
        assert result.success, f"Dry run failed: {result.stderr}"
        assert 'DRY RUN' in result.stdout
        assert 'SUMMARY' in result.stdout
    
    def test_depth_argument_parsing(self):
        """Test various depth argument combinations."""
        # Single depth
        result = run_cli(str(self.temp_dir), '--depth', '1', '--dry-run')
        assert result.success, f"Single depth failed: {result.stderr}"
        assert 'Depths:        [1]' in result.stdout
        
        # Multiple depths
        result = run_cli(str(self.temp_dir), '--depth', '0', '--depth', '2', '--dry-run')
        assert result.success, f"Multiple depths failed: {result.stderr}"
        assert 'Depths:        [0, 2]' in result.stdout or '[0,2]' in result.stdout
        
        # Depth range
        result = run_cli(str(self.temp_dir), '--depth-to', '2', '--dry-run')
        assert result.success, f"Depth range failed: {result.stderr}"
        assert '[0, 1, 2]' in result.stdout or 'Depths:' in result.stdout
    
    def test_strategy_selection(self):
        """Test strategy argument parsing.""" 
        for strategy in ['shallow', 'deep', 'smart']:
            result = run_cli(str(self.temp_dir), '--strategy', strategy, '--dry-run')
            assert result.success, f"Strategy {strategy} failed: {result.stderr}"
            assert f'Strategy:      {strategy}' in result.stdout
    
    def test_analyze_parameter(self):
        """Test --analyze parameter."""
        for analyze in ['auto', 'tree', 'folder-only', 'low-memory']:
            result = run_cli(str(self.temp_dir), '--analyze', analyze, '--dry-run')
            assert result.success, f"Analyze {analyze} failed: {result.stderr}"
            # Should run without crashing
    
    def test_convenience_aliases(self):
        """Test convenience alias arguments."""
        # Test --fix-all
        result = run_cli(str(self.temp_dir), '--fix-all', '--dry-run')
        assert result.success, f"--fix-all failed: {result.stderr}"
        assert 'Strategy:      deep' in result.stdout
        
        # Test --fix-2
        result = run_cli(str(self.temp_dir), '--fix-2', '--dry-run')
        assert result.success, f"--fix-2 failed: {result.stderr}"
        assert 'Strategy:      deep' in result.stdout
        assert '[0, 1]' in result.stdout
        
        # Test --fix-immediate
        result = run_cli(str(self.temp_dir), '--fix-immediate', '--dry-run')
        assert result.success, f"--fix-immediate failed: {result.stderr}"
        assert 'Strategy:      shallow' in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""
    
    def test_nonexistent_path(self):
        """Test handling of non-existent paths."""
        result = run_cli('/nonexistent/path/12345', '--dry-run')
        assert not result.success, "Should fail for non-existent path"
        assert 'ERROR' in result.stderr or 'does not exist' in result.stderr
    
    def test_invalid_depth_values(self):
        """Test handling of invalid depth values."""
        result = run_cli('.', '--depth', 'invalid', '--dry-run')
        assert not result.success, "Should fail for invalid depth"
        assert 'error' in result.stderr.lower() or 'invalid' in result.stderr.lower()
    
    def test_invalid_strategy(self):
        """Test handling of invalid strategy values."""
        result = run_cli('.', '--strategy', 'invalid', '--dry-run')
        assert not result.success, "Should fail for invalid strategy" 
        assert 'error' in result.stderr.lower() or 'invalid choice' in result.stderr.lower()
    
    def test_conflicting_arguments(self):
        """Test handling of conflicting arguments."""
        result = run_cli('.', '--quiet', '--verbose', '--dry-run')
        assert not result.success, "Should fail for conflicting quiet/verbose"
        assert 'mutually exclusive' in result.stderr.lower() or 'error' in result.stderr.lower()


class TestCLIExclusionOptions:
    """Test CLI exclusion and filtering options."""
    
    def setup_method(self):
        """Create temporary test directory with system files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.folders = create_test_folder_structure(self.temp_dir)
        
        # Add some system files
        thumbs_file = self.folders['with_files'] / 'Thumbs.db'
        thumbs_file.write_text('system file')
        
        desktop_file = self.folders['with_files'] / 'desktop.ini'
        desktop_file.write_text('[.ShellClassInfo]')
    
    def teardown_method(self):
        """Clean up temporary test directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_exclude_mode_options(self):
        """Test different exclusion modes."""
        for mode in ['default', 'none', 'files', 'folders']:
            result = run_cli(str(self.temp_dir), '--exclude-mode', mode, '--dry-run')
            assert result.success, f"Exclude mode {mode} failed: {result.stderr}"
            assert f'Mode={mode}' in result.stdout
    
    def test_include_generated_legacy_option(self):
        """Test legacy --include-generated option."""
        result = run_cli(str(self.temp_dir), '--include-generated', '--dry-run')
        assert result.success, f"--include-generated failed: {result.stderr}"
        # Should show deprecation notice
        assert 'deprecated' in result.stdout.lower() or 'Mode=none' in result.stdout
    
    def test_custom_exclude_patterns(self):
        """Test custom exclusion patterns."""
        result = run_cli(str(self.temp_dir), '--exclude', '*.tmp,*.bak', '--dry-run')
        assert result.success, f"Custom exclude failed: {result.stderr}"
        assert 'Exclude=' in result.stdout


class TestCLIOutputOptions:
    """Test CLI output and reporting options."""
    
    def setup_method(self):
        """Create temporary test directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.folders = create_test_folder_structure(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary test directory.""" 
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_verbose_levels(self):
        """Test different verbosity levels."""
        for v_level in ['-v', '-vv', '-vvv']:
            result = run_cli(str(self.temp_dir), v_level, '--dry-run')
            assert result.success, f"Verbose level {v_level} failed: {result.stderr}"
    
    def test_quiet_mode(self):
        """Test quiet mode suppresses output."""
        result = run_cli(str(self.temp_dir), '--quiet', '--dry-run')
        assert result.success, f"Quiet mode failed: {result.stderr}"
        # Should have minimal output (just summary or nothing)
        assert len(result.stdout.strip()) < 1000  # Arbitrary threshold for "quiet"
    
    def test_report_generation(self):
        """Test report file generation."""
        report_file = self.temp_dir / 'test_report.csv'
        result = run_cli(str(self.temp_dir), '--report', str(report_file), '--dry-run')
        assert result.success, f"Report generation failed: {result.stderr}"
        assert report_file.exists(), "Report file was not created"
        
        # Check report content
        content = report_file.read_text()
        assert 'Path,Original Time,New Time,Status' in content
    
    def test_visualize_mode(self):
        """Test visualization mode."""
        result = run_cli(str(self.temp_dir), '--visualize')
        assert result.success, f"Visualize mode failed: {result.stderr}"
        assert 'VISUALIZATION STATISTICS' in result.stdout


def run_all_cli_tests():
    """
    Run all CLI integration tests.
    
    This function can be called from other test runners.
    """
    import pytest
    
    test_classes = [
        TestCLIBasicFunctionality,
        TestCLIArgumentParsing, 
        TestCLIErrorHandling,
        TestCLIExclusionOptions,
        TestCLIOutputOptions
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*60}")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            print(f"  {method_name}...", end=' ')
            
            try:
                # Create instance and run setup
                instance = test_class()
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()
                
                # Run the test
                test_method = getattr(instance, method_name)
                test_method()
                
                print("PASS")
                total_passed += 1
                
            except Exception as e:
                print(f"FAIL - {e}")
                total_failed += 1
            
            finally:
                # Run teardown
                if hasattr(instance, 'teardown_method'):
                    instance.teardown_method()
    
    print(f"\n{'='*60}")
    print(f"CLI INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Total:  {total_passed + total_failed}")
    
    if total_failed > 0:
        print(f"\n[FAILURE] {total_failed} CLI integration tests failed")
        return 1
    else:
        print(f"\n[SUCCESS] All CLI integration tests passed")
        return 0


if __name__ == '__main__':
    sys.exit(run_all_cli_tests())