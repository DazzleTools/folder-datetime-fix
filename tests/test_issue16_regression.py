#!/usr/bin/env python
"""
Regression Test for DazzleTreeLib Issue #16
============================================

Ensures that filesystem errors properly propagate to error handling policies.
This was a critical bug where AsyncFileSystemAdapter silently swallowed errors,
preventing ErrorHandlingAdapter from applying error policies.

DazzleTreeLib Issue #16: Silent error swallowing breaks error handling system
"""

import pytest
import asyncio
import tempfile
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil


class TestIssue16Regression(unittest.TestCase):
    """Test that DazzleTreeLib Issue #16 (silent error swallowing) remains fixed."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix='issue16_regression_')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_permission_errors_propagate_correctly(self):
        """Test that permission errors are handled by error policies, not swallowed."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                AsyncFileSystemNode,
                ErrorHandlingAdapter,
                ContinueOnErrorsPolicy
            )
            
            # Create base adapter
            base_adapter = AsyncFileSystemAdapter()
            
            # Mock os.scandir to simulate permission error
            with patch('os.scandir') as mock_scandir:
                mock_scandir.side_effect = PermissionError("Permission denied")
                
                # Without error handling, should raise
                test_node = AsyncFileSystemNode(Path(self.test_dir))
                
                # Test 1: Base adapter should propagate errors (not swallow them)
                error_raised = False
                try:
                    async for _ in base_adapter.get_children(test_node):
                        pass
                except PermissionError:
                    error_raised = True
                
                self.assertTrue(error_raised, 
                              "Base adapter must propagate errors, not swallow them")
                
                # Test 2: With error handling policy, should handle gracefully
                policy = ContinueOnErrorsPolicy(verbose=False)
                adapter = ErrorHandlingAdapter(base_adapter, policy)
                
                children = []
                error_in_iteration = False
                try:
                    async for child in adapter.get_children(test_node):
                        children.append(child)
                except PermissionError:
                    error_in_iteration = True
                
                # ContinueOnErrors should not raise
                self.assertFalse(error_in_iteration, 
                               "ContinueOnErrors should handle errors gracefully")
                
                # Policy should have recorded the error
                self.assertGreater(len(policy.errors), 0, 
                                 "Policy should record errors")
                
                # Verify error type
                if policy.errors:
                    self.assertEqual(policy.errors[0]['error_type'], 'PermissionError')
        
        # Run the async test
        asyncio.run(run_test())
    
    def test_oserror_not_silently_ignored(self):
        """Test that OSError is properly handled, not ignored."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                AsyncFileSystemNode,
                ErrorHandlingAdapter,
                FailFastPolicy
            )
            
            # Create base adapter
            base_adapter = AsyncFileSystemAdapter()
            
            # Mock os.scandir to simulate OSError
            with patch('os.scandir') as mock_scandir:
                mock_scandir.side_effect = OSError("I/O error")
                
                # Create error handling with FailFast policy
                policy = FailFastPolicy()
                adapter = ErrorHandlingAdapter(base_adapter, policy)
                
                test_node = AsyncFileSystemNode(Path(self.test_dir))
                
                # FailFast should immediately propagate the error
                error_type = None
                try:
                    async for _ in adapter.get_children(test_node):
                        pass
                except OSError as e:
                    error_type = type(e).__name__
                
                self.assertEqual(error_type, "OSError", 
                               "FailFast policy should propagate OSError")
        
        # Run the async test
        asyncio.run(run_test())
    
    def test_mixed_success_and_failure(self):
        """Test handling mix of successful and failed directory access."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                AsyncFileSystemNode,
                ErrorHandlingAdapter,
                ContinueOnErrorsPolicy
            )
            
            # Create test structure
            good_dir = Path(self.test_dir) / "good"
            good_dir.mkdir()
            (good_dir / "file.txt").write_text("content")
            
            bad_dir = Path(self.test_dir) / "bad"
            bad_dir.mkdir()
            
            # Mock scandir to fail only for "bad" directory
            original_scandir = os.scandir
            
            def selective_scandir(path):
                if "bad" in str(path):
                    raise PermissionError(f"Cannot access {path}")
                return original_scandir(path)
            
            with patch('os.scandir', side_effect=selective_scandir):
                # Create adapter with ContinueOnErrors
                base_adapter = AsyncFileSystemAdapter()
                policy = ContinueOnErrorsPolicy(verbose=False)
                adapter = ErrorHandlingAdapter(base_adapter, policy)
                
                # Traverse test directory
                test_node = AsyncFileSystemNode(Path(self.test_dir))
                found_dirs = []
                
                async for child in adapter.get_children(test_node):
                    found_dirs.append(child.path.name)
                    # Try to get children of each subdirectory
                    async for _ in adapter.get_children(child):
                        pass
                
                # Should find "good" directory
                self.assertIn("good", found_dirs, "Should find accessible directory")
                
                # Should also find "bad" directory (listing works, accessing fails)
                self.assertIn("bad", found_dirs, "Should list all directories")
                
                # Should have error for accessing "bad" directory's contents
                self.assertGreater(len(policy.errors), 0, 
                                 "Should record permission error for bad directory")
                
                # Verify we got permission error
                permission_errors = [e for e in policy.errors 
                                   if e['error_type'] == 'PermissionError']
                self.assertGreater(len(permission_errors), 0, 
                                 "Should have PermissionError for bad directory")
        
        # Run the async test
        asyncio.run(run_test())
    
    @pytest.mark.skipif(sys.platform == "win32", 
                       reason="Permission testing unreliable on Windows")
    def test_real_permission_error_handling(self):
        """Test with actual filesystem permission restrictions."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                AsyncFileSystemNode,
                ErrorHandlingAdapter,
                CollectErrorsPolicy
            )
            
            # Create restricted directory
            restricted = Path(self.test_dir) / "restricted"
            restricted.mkdir()
            (restricted / "secret.txt").write_text("secret")
            
            # Remove read permission (Unix only)
            os.chmod(restricted, 0o000)
            
            try:
                # Create adapter with error collection
                base_adapter = AsyncFileSystemAdapter()
                policy = CollectErrorsPolicy()
                adapter = ErrorHandlingAdapter(base_adapter, policy)
                
                # Try to access restricted directory
                test_node = AsyncFileSystemNode(restricted)
                children = []
                
                async for child in adapter.get_children(test_node):
                    children.append(child)
                
                # Should not get any children
                self.assertEqual(len(children), 0, 
                               "Should not access restricted directory")
                
                # Should have collected the error
                self.assertGreater(len(policy.errors), 0, 
                                 "Should collect permission error")
                
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted, 0o755)
        
        # Run the async test if not on Windows
        if sys.platform != "win32":
            asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()