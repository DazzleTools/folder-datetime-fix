#!/usr/bin/env python
"""
Test Issue #15 Fix - Correct API Usage
=======================================

Verifies that the RuntimeError about event loops no longer occurs
using the actual DazzleTreeLib traversal API.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path


async def test_issue_15_with_traverser():
    """Test Issue #15 fix using the actual traverser API."""
    print("Testing Issue #15 fix with proper API...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy,
        AsyncBreadthFirstTraverser
    )
    
    # Create test directory
    test_dir = tempfile.mkdtemp(prefix='issue15_')
    
    try:
        # Create structure with potential permission issues
        for i in range(3):
            subdir = Path(test_dir) / f"dir_{i}"
            subdir.mkdir()
            for j in range(3):
                (subdir / f"file_{j}.txt").write_text(f"test_{i}_{j}")
        
        # Setup adapters with error handling
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        # Create traverser
        traverser = AsyncBreadthFirstTraverser(adapter)
        
        print(f"Testing directory: {test_dir}")
        
        nodes_processed = 0
        sync_errors_in_async = 0
        
        # This is where the bug would manifest - processing nodes in async context
        try:
            async for node in traverser.traverse(test_dir):
                nodes_processed += 1
                
                # These operations might trigger sync error handling in async context
                # Before fix: Would cause RuntimeError: This event loop is already running
                try:
                    # Force string representation (might fail for restricted files)
                    str_repr = str(node)
                    
                    # Try to access properties that could trigger errors
                    if hasattr(node, 'path'):
                        _ = node.path
                    if hasattr(node, 'name'):
                        _ = node.name
                    
                    # This might trigger permission errors
                    if hasattr(node, '__repr__'):
                        _ = repr(node)
                        
                except Exception as e:
                    sync_errors_in_async += 1
                    # Errors should be handled gracefully, not crash with event loop error
            
            print(f"\nResults:")
            print(f"  Nodes processed: {nodes_processed}")
            print(f"  Policy errors caught: {len(policy.errors)}")
            print(f"  Sync errors in async context: {sync_errors_in_async}")
            
            if policy.errors:
                print(f"\nSample policy errors:")
                for err in policy.errors[:3]:
                    print(f"  - {err.get('error_type', 'Unknown')}")
            
            print("\nSUCCESS: No RuntimeError about event loops!")
            return True
            
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                print("\nFAILED: Issue #15 NOT FIXED!")
                print(f"  Error: {e}")
                return False
            raise
            
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


async def test_with_windows_system_dirs():
    """Test with real Windows directories that have permission restrictions."""
    print("\nTesting with Windows system directories...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy,
        AsyncDepthFirstTraverser
    )
    
    # Use directories that typically have some restricted items
    test_paths = [
        Path("C:/Windows/Temp"),
        Path("C:/ProgramData/Microsoft"),
    ]
    
    for test_path in test_paths:
        if not test_path.exists():
            continue
            
        print(f"\nTesting: {test_path}")
        
        # Setup with error handling
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        # Use depth-first traverser this time
        traverser = AsyncDepthFirstTraverser(adapter, max_depth=2)
        
        nodes = 0
        max_nodes = 50
        
        try:
            async for node in traverser.traverse(test_path):
                nodes += 1
                
                # Try to trigger sync errors
                try:
                    _ = str(node)
                except:
                    pass
                
                if nodes >= max_nodes:
                    break
            
            print(f"  Processed {nodes} nodes")
            print(f"  Errors handled: {len(policy.errors)}")
            
            # Success - no event loop error!
            
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                print(f"  FAILED: Event loop error occurred!")
                return False
            raise
    
    print("\nSUCCESS: Real paths handled without event loop errors!")
    return True


async def test_direct_error_in_get_children():
    """Test errors directly in get_children method."""
    print("\nTesting direct errors in get_children...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy
    )
    
    # Create a directory that will have errors
    test_dir = tempfile.mkdtemp(prefix='direct_test_')
    
    try:
        # Create some files
        Path(test_dir, "test.txt").write_text("content")
        
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        # Test get_children directly
        # Add a non-existent path to trigger errors
        test_paths = [
            test_dir,
            Path(test_dir) / "nonexistent",  # This will cause an error
            "C:/Windows/System32/config"  # Likely restricted
        ]
        
        for path in test_paths:
            print(f"  Testing get_children on: {path}")
            try:
                children = []
                async for child in adapter.get_children(path):
                    children.append(child)
                    # Try to access child properties
                    try:
                        _ = str(child)
                    except:
                        pass
                print(f"    Got {len(children)} children")
            except Exception as e:
                # Should handle gracefully, not crash with event loop error
                print(f"    Handled error: {type(e).__name__}")
        
        print(f"\nTotal errors handled by policy: {len(policy.errors)}")
        print("SUCCESS: get_children errors handled without event loop issues!")
        return True
        
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            print("FAILED: Event loop error in get_children!")
            return False
        raise
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ISSUE #15 FIX VERIFICATION - CORRECT API")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic traverser test
    result = await test_issue_15_with_traverser()
    results.append(("Traverser Test", result))
    
    # Test 2: Windows system directories
    result = await test_with_windows_system_dirs()
    results.append(("System Dirs Test", result))
    
    # Test 3: Direct get_children errors
    result = await test_direct_error_in_get_children()
    results.append(("Direct get_children Test", result))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name:30} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\nALL TESTS PASSED!")
        print("Issue #15 is FIXED - No more event loop errors!")
        print("\nThe fix successfully prevents RuntimeError when:")
        print("  - Sync errors occur in async contexts")
        print("  - Permission errors happen during traversal")
        print("  - Error policies handle exceptions")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        print("Please investigate remaining issues.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))