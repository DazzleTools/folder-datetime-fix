#!/usr/bin/env python
"""
Regression Test for Issue #15
==============================

Ensures that sync errors in async context don't cause event loop crashes.
This was a critical bug that caused RuntimeError: This event loop is already running.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import unittest


class MockNodeThatFails:
    """Mock node that fails on string conversion."""
    def __str__(self):
        raise PermissionError("Cannot convert to string")
    
    def __repr__(self):
        raise PermissionError("Cannot get representation")


class TestIssue15Regression(unittest.TestCase):
    """Test that Issue #15 (event loop crash) remains fixed."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix='issue15_test_')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sync_errors_in_async_context_handled_gracefully(self):
        """Test that sync errors in async context don't crash the event loop."""
        async def run_test():
            from dazzletreelib.aio import (
                ErrorHandlingAdapter,
                ContinueOnErrorsPolicy
            )
            
            # Create a mock adapter that will trigger sync errors
            class MockAdapter:
                async def get_children(self, node):
                    """Return children, some of which will fail."""
                    yield "normal_node_1"
                    yield "normal_node_2"
                    yield MockNodeThatFails()  # This will trigger sync errors
                    yield "normal_node_3"
                
                def sync_method(self, node):
                    """A sync method that might fail."""
                    if isinstance(node, MockNodeThatFails):
                        raise PermissionError("Sync method failed")
                    return f"processed_{node}"
            
            # Setup error handling
            base_adapter = MockAdapter()
            policy = ContinueOnErrorsPolicy(verbose=False)
            adapter = ErrorHandlingAdapter(base_adapter, policy)
            
            nodes_processed = 0
            runtime_error_occurred = False
            permission_errors_caught = 0
            
            try:
                # Process nodes in async context
                async for node in adapter.get_children("root"):
                    nodes_processed += 1
                    
                    # Try to trigger sync errors within async context
                    # This is what would cause the RuntimeError before the fix
                    try:
                        _ = str(node)
                        _ = repr(node)
                        # Note: adapter.sync_method isn't wrapped by ErrorHandlingAdapter
                        # so we call it directly on base_adapter
                        _ = base_adapter.sync_method(node)
                    except PermissionError:
                        # These errors should be handled gracefully
                        # NOT crash with "RuntimeError: This event loop is already running"
                        permission_errors_caught += 1
                    except RuntimeError as e:
                        if "This event loop is already running" in str(e):
                            runtime_error_occurred = True
                            raise
            
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    runtime_error_occurred = True
                    raise
            
            # Verify results
            self.assertEqual(nodes_processed, 4, "Should have processed 4 nodes")
            self.assertFalse(runtime_error_occurred, "Should not have RuntimeError about event loops")
            self.assertGreater(permission_errors_caught, 0, "Should have caught permission errors")
            
            return True
        
        # Run the async test
        result = asyncio.run(run_test())
        self.assertTrue(result, "Test should complete successfully")
    
    def test_real_filesystem_traversal_no_event_loop_errors(self):
        """Test that real filesystem traversal doesn't trigger event loop errors."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                ErrorHandlingAdapter,
                ContinueOnErrorsPolicy,
                AsyncBreadthFirstTraverser
            )
            
            # Create test structure
            Path(self.test_dir, "file1.txt").write_text("content1")
            Path(self.test_dir, "file2.txt").write_text("content2")
            subdir = Path(self.test_dir, "subdir")
            subdir.mkdir()
            Path(subdir, "file3.txt").write_text("content3")
            
            # Setup adapters
            base_adapter = AsyncFileSystemAdapter()
            policy = ContinueOnErrorsPolicy(verbose=False)
            adapter = ErrorHandlingAdapter(base_adapter, policy)
            
            # Create traverser
            traverser = AsyncBreadthFirstTraverser()
            
            nodes_processed = 0
            runtime_error_occurred = False
            
            try:
                # Use correct API - pass both root and adapter
                async for node in traverser.traverse(self.test_dir, adapter):
                    nodes_processed += 1
                    
                    # Try operations that might fail
                    try:
                        _ = str(node)
                        if hasattr(node, 'path'):
                            _ = node.path
                    except Exception as e:
                        # Check for the specific RuntimeError
                        if isinstance(e, RuntimeError) and "This event loop is already running" in str(e):
                            runtime_error_occurred = True
                            raise
                        # Other errors are fine - handled by policy
                        pass
            
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    runtime_error_occurred = True
                    raise
            
            # Verify traversal worked without event loop errors
            self.assertGreater(nodes_processed, 0, "Should have traversed some nodes")
            self.assertFalse(runtime_error_occurred, "Should not have RuntimeError about event loops")
            
            return True
        
        # Run the async test
        result = asyncio.run(run_test())
        self.assertTrue(result, "Filesystem traversal should complete without event loop errors")
    
    @pytest.mark.slow
    def test_permission_errors_in_async_dont_crash(self):
        """Test that permission errors in async context are handled properly."""
        async def run_test():
            from dazzletreelib.aio import (
                AsyncFileSystemAdapter,
                ErrorHandlingAdapter,
                ContinueOnErrorsPolicy
            )
            
            # Test with paths that might have permission issues
            # Using Windows temp directory which usually has some restricted items
            test_path = Path("C:/Windows/Temp")
            if not test_path.exists():
                # Skip test if path doesn't exist
                return True
            
            base_adapter = AsyncFileSystemAdapter()
            policy = ContinueOnErrorsPolicy(verbose=False)
            adapter = ErrorHandlingAdapter(base_adapter, policy)
            
            nodes_checked = 0
            max_nodes = 20  # Limit for performance
            runtime_error_occurred = False
            
            try:
                async for child in adapter.get_children(test_path):
                    nodes_checked += 1
                    
                    # Try to access properties that might fail
                    try:
                        _ = str(child)
                    except Exception as e:
                        if isinstance(e, RuntimeError) and "This event loop is already running" in str(e):
                            runtime_error_occurred = True
                            raise
                        # Other errors are expected and handled
                        pass
                    
                    if nodes_checked >= max_nodes:
                        break
            
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    runtime_error_occurred = True
                    raise
            except Exception:
                # Other exceptions are fine - permission errors, etc.
                pass
            
            self.assertFalse(runtime_error_occurred, "Should not have event loop RuntimeError")
            
            return True
        
        # Run the async test
        result = asyncio.run(run_test())
        self.assertTrue(result, "Permission errors should be handled without crashing event loop")


if __name__ == "__main__":
    unittest.main()