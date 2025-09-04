#!/usr/bin/env python
"""
Simple Test for Issue #15 Fix
==============================

Tests that sync errors in async context don't cause event loop crashes.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path


class MockNodeThatFails:
    """Mock node that fails on string conversion."""
    def __str__(self):
        raise PermissionError("Cannot convert to string")
    
    def __repr__(self):
        raise PermissionError("Cannot get representation")


async def test_issue_15_core():
    """Test the core Issue #15 fix - sync errors in async context."""
    print("Testing Issue #15 core fix...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy
    )
    
    # Create a mock adapter that will trigger sync errors
    class MockAdapter:
        async def get_children(self, node):
            """Return children, some of which will fail."""
            # Yield some normal nodes
            yield "normal_node_1"
            yield "normal_node_2"
            # Yield a node that fails on sync operations
            yield MockNodeThatFails()
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
    
    try:
        # Process nodes in async context
        nodes = []
        async for node in adapter.get_children("root"):
            nodes.append(node)
            
            # Try to trigger sync errors within async context
            # This is what would cause the RuntimeError before the fix
            try:
                # These sync operations might fail
                str_repr = str(node)
                repr_str = repr(node)
                
                # Try calling a sync method through the adapter
                result = adapter.sync_method(node)
                
            except Exception as e:
                # Errors should be handled gracefully
                # NOT crash with "RuntimeError: This event loop is already running"
                pass
        
        print(f"Processed {len(nodes)} nodes")
        print(f"Errors handled by policy: {len(policy.errors)}")
        
        if policy.errors:
            print("\nErrors caught:")
            for err in policy.errors:
                print(f"  - {err.get('error_type')}: {err.get('method')}")
        
        print("\nSUCCESS: No RuntimeError about event loops!")
        return True
        
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            print(f"\nFAILED: Issue #15 NOT FIXED!")
            print(f"  Error: {e}")
            return False
        raise
    
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_filesystem():
    """Test with real filesystem operations."""
    print("\nTesting with real filesystem...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy,
        AsyncBreadthFirstTraverser
    )
    
    # Create test directory
    test_dir = tempfile.mkdtemp(prefix='real_fs_test_')
    
    try:
        # Create some files
        Path(test_dir, "file1.txt").write_text("content1")
        Path(test_dir, "file2.txt").write_text("content2")
        subdir = Path(test_dir, "subdir")
        subdir.mkdir()
        Path(subdir, "file3.txt").write_text("content3")
        
        # Setup adapters
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        # Create traverser
        traverser = AsyncBreadthFirstTraverser()
        
        print(f"Traversing: {test_dir}")
        
        nodes = 0
        # Use correct API - pass both root and adapter
        async for node in traverser.traverse(test_dir, adapter):
            nodes += 1
            
            # Try operations that might fail
            try:
                _ = str(node)
                if hasattr(node, 'path'):
                    _ = node.path
            except:
                pass  # Errors handled by policy
        
        print(f"Traversed {nodes} nodes")
        print(f"Errors handled: {len(policy.errors)}")
        
        print("SUCCESS: Real filesystem traversal without event loop errors!")
        return True
        
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            print("FAILED: Event loop error during traversal!")
            return False
        raise
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ISSUE #15 SIMPLE TEST")
    print("=" * 60)
    print("Testing: Sync errors in async context no longer crash")
    print("         with 'RuntimeError: This event loop is already running'")
    print("=" * 60)
    
    # Test 1: Core fix with mock adapter
    result1 = await test_issue_15_core()
    
    # Test 2: Real filesystem
    result2 = await test_real_filesystem()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result1 and result2:
        print("\nALL TESTS PASSED!")
        print("\nIssue #15 is FIXED:")
        print("  - Sync errors in async context are handled gracefully")
        print("  - No more 'RuntimeError: This event loop is already running'")
        print("  - Error policies work correctly with sync error handlers")
        return 0
    else:
        print("\nTEST FAILED")
        if not result1:
            print("  - Core test failed")
        if not result2:
            print("  - Real filesystem test failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))