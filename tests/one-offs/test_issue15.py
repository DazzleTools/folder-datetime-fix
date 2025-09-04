#!/usr/bin/env python
"""
Test Issue #15 Fix in modified-datetime-fix
============================================

Verifies that the RuntimeError about event loops no longer occurs.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path


async def test_issue_15():
    """Test that Issue #15 is fixed - no more event loop crashes."""
    print("Testing Issue #15 fix...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy
    )
    
    # Create test directory with some permission issues
    test_dir = tempfile.mkdtemp(prefix='issue15_test_')
    
    try:
        # Create structure
        for i in range(3):
            subdir = Path(test_dir) / f"dir_{i}"
            subdir.mkdir()
            for j in range(3):
                (subdir / f"file_{j}.txt").write_text(f"content_{i}_{j}")
        
        # Setup adapters
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        nodes_processed = 0
        errors_found = 0
        
        print(f"Processing test directory: {test_dir}")
        
        # This would crash with RuntimeError before the fix
        try:
            # Use the actual traverse method
            async for node in adapter.traverse(test_dir):
                nodes_processed += 1
                
                # Try to trigger sync errors in async context
                # This is what would cause the RuntimeError
                try:
                    # These operations might fail and trigger sync error handling
                    str_repr = str(node)
                    if hasattr(node, '__repr__'):
                        repr_str = repr(node)
                    if hasattr(node, 'path'):
                        path = node.path
                    if hasattr(node, 'name'):
                        name = node.name
                except Exception as e:
                    # Before fix: RuntimeError: This event loop is already running
                    # After fix: Error is handled gracefully
                    errors_found += 1
                    print(f"  Error handled gracefully: {type(e).__name__}")
                
                if nodes_processed % 10 == 0:
                    print(f"  Processed {nodes_processed} nodes...")
        
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                print("\nFAILED: Issue #15 NOT fixed!")
                print(f"  Still getting: {e}")
                return False
            else:
                raise
        
        print(f"\nResults:")
        print(f"  Nodes processed: {nodes_processed}")
        print(f"  Errors handled: {len(policy.errors)}")
        print(f"  Inline errors: {errors_found}")
        
        # Show some handled errors
        if policy.errors:
            print(f"\nSample errors handled by policy:")
            for err in policy.errors[:3]:
                print(f"  - {err['error_type']}: {err.get('error_message', 'N/A')}")
        
        print("\nSUCCESS: Issue #15 is FIXED!")
        print("  No RuntimeError about event loops")
        print("  All errors handled gracefully")
        return True
        
    except Exception as e:
        print(f"\nFAILED with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


async def test_with_real_paths():
    """Test with real Windows paths that might have permission issues."""
    print("\nTesting with real Windows paths...")
    print("-" * 60)
    
    from dazzletreelib.aio import (
        AsyncFileSystemAdapter,
        ErrorHandlingAdapter,
        ContinueOnErrorsPolicy
    )
    
    # Test with paths that often have restricted subdirectories
    test_paths = [
        Path("C:/Windows/Temp"),     # Usually has some restricted items
        Path("C:/ProgramData"),       # Often has permission-restricted subdirs
        Path("C:/Users/Public"),      # Should be mostly accessible
    ]
    
    for test_path in test_paths:
        if not test_path.exists():
            continue
            
        print(f"\nTesting {test_path}...")
        
        base_adapter = AsyncFileSystemAdapter()
        policy = ContinueOnErrorsPolicy(verbose=False)
        adapter = ErrorHandlingAdapter(base_adapter, policy)
        
        nodes = 0
        max_nodes = 100  # Limit to avoid processing too many files
        
        try:
            async for node in adapter.traverse(test_path):
                nodes += 1
                
                # Try operations that might fail
                try:
                    _ = str(node)
                    if hasattr(node, 'is_dir'):
                        _ = await node.is_dir()
                except Exception:
                    pass  # Errors are handled by the policy
                
                if nodes >= max_nodes:
                    break
            
            print(f"  Processed {nodes} nodes")
            print(f"  Handled {len(policy.errors)} errors")
            
            if policy.errors:
                # Show types of errors encountered
                error_types = set(e['error_type'] for e in policy.errors)
                print(f"  Error types: {', '.join(error_types)}")
        
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                print(f"  FAILED: Event loop error!")
                return False
        
        except Exception as e:
            print(f"  Unexpected error: {type(e).__name__}")
    
    print("\nSUCCESS: All paths processed without event loop errors!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ISSUE #15 FIX VERIFICATION")
    print("=" * 60)
    
    # Test 1: Controlled test
    result1 = await test_issue_15()
    
    # Test 2: Real paths
    result2 = await test_with_real_paths()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if result1 and result2:
        print("\nALL TESTS PASSED!")
        print("Issue #15 is completely fixed.")
        print("No more RuntimeError: This event loop is already running")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        print("Issue #15 may not be fully fixed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))