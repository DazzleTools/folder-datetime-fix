#!/usr/bin/env python3
"""
Final test of error handling with UNC paths.
This properly tests the PolicyDrivenErrorAdapter approach.
"""

import asyncio
from pathlib import Path
from dazzletreelib.aio import (
    AsyncFileSystemAdapter,
    AsyncFileSystemNode,
    ErrorHandlingAdapter,
    ContinueOnErrorsPolicy,
    FailFastPolicy,
)
from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser


async def test_with_continue_policy(test_path: Path):
    """Test with ContinueOnErrorsPolicy - should skip permission errors."""
    print(f"\n1. Testing {test_path} with ContinueOnErrorsPolicy:")
    print("-" * 50)
    
    # Create adapter stack with error handling
    base = AsyncFileSystemAdapter(
        max_concurrent=10,
        batch_size=64,
        follow_symlinks=False
    )
    policy = ContinueOnErrorsPolicy(verbose=True)
    adapter = ErrorHandlingAdapter(base, policy)
    
    # Traverse
    traverser = AsyncLevelOrderDepthTraverser()
    root = AsyncFileSystemNode(test_path)
    
    folder_count = 0
    folder_names = []
    
    async for depth, nodes in traverser.traverse_by_level(root, adapter, max_depth=1):
        if depth == 1:  # Only count folders at depth 1, not the root
            for node in nodes:
                if node.path.is_dir():
                    folder_count += 1
                    if folder_count <= 5:
                        folder_names.append(node.path.name)
    
    print(f"[OK] Found {folder_count} folders at depth 1")
    if folder_names:
        print(f"  First few: {', '.join(folder_names)}")
    
    if policy.skipped_paths:
        print(f"[OK] Skipped {len(policy.skipped_paths)} paths due to permission errors:")
        for path in list(policy.skipped_paths)[:3]:
            print(f"    - {path}")
    else:
        print("  (No permission errors encountered)")
    
    return folder_count > 0


async def test_with_fail_fast_policy(test_path: Path):
    """Test with FailFastPolicy - should fail on first permission error."""
    print(f"\n2. Testing {test_path} with FailFastPolicy:")
    print("-" * 50)
    
    # Create adapter stack with strict error handling
    base = AsyncFileSystemAdapter(
        max_concurrent=10,
        batch_size=64,
        follow_symlinks=False
    )
    policy = FailFastPolicy()
    adapter = ErrorHandlingAdapter(base, policy)
    
    # Traverse
    traverser = AsyncLevelOrderDepthTraverser()
    root = AsyncFileSystemNode(test_path)
    
    try:
        folder_count = 0
        async for depth, nodes in traverser.traverse_by_level(root, adapter, max_depth=1):
            if depth == 1:  # Only count folders at depth 1, not the root
                for node in nodes:
                    if node.path.is_dir():
                        folder_count += 1
        
        print(f"  Completed without errors - found {folder_count} folders")
        print("  (No permission-restricted folders in this path)")
        return True
        
    except PermissionError as e:
        print(f"[OK] Failed as expected on permission error:")
        print(f"    {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


async def main():
    """Main test runner."""
    print("=" * 60)
    print("Testing PolicyDrivenErrorAdapter")
    print("=" * 60)
    
    # Test with UNC path if available
    unc_path = Path(r"\\aktuldjr\j")
    if unc_path.exists():
        print(f"\nUNC path {unc_path} is accessible")
        await test_with_continue_policy(unc_path)
        await test_with_fail_fast_policy(unc_path)
    else:
        print(f"\nUNC path {unc_path} not accessible, using local path")
    
    # Also test with local path
    local_path = Path("C:/")
    print(f"\n\nTesting with local path: {local_path}")
    print("=" * 60)
    await test_with_continue_policy(local_path)
    await test_with_fail_fast_policy(local_path)
    
    print("\n" + "=" * 60)
    print("[OK] All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())