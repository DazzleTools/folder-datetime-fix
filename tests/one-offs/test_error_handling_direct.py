#!/usr/bin/env python3
"""
Direct test of the error handling without going through all the imports.
"""

import sys
import asyncio
from pathlib import Path

# Add upstream DazzleTreeLib to path first
sys.path.insert(0, "C:/code/DazzleTreeLib")

# Now import what we need
from dazzletreelib.aio import (
    AsyncFileSystemAdapter,
    AsyncFileSystemNode,
)
from dazzletreelib.aio.core.depth_traverser import AsyncLevelOrderDepthTraverser

# Add our local extensions
sys.path.insert(0, "C:/code/modified_datetime_fix/local")
from dazzletreelib.aio.error_handling import ErrorHandlingAdapter
from dazzletreelib.aio.error_policies import ContinueOnErrorsPolicy, FailFastPolicy


async def test_error_handling():
    """Test error handling with UNC paths."""
    
    # Test path - use local path for now
    test_path = Path("C:/code")
    
    print(f"Testing path: {test_path}")
    print("-" * 60)
    
    # Create base adapter
    base_adapter = AsyncFileSystemAdapter(
        max_concurrent=50,
        batch_size=256,
        follow_symlinks=False
    )
    
    # Test 1: With ContinueOnErrorsPolicy (should skip errors)
    print("\n1. Testing with ContinueOnErrorsPolicy:")
    policy = ContinueOnErrorsPolicy(verbose=True)
    adapter = ErrorHandlingAdapter(base_adapter, policy)
    
    traverser = AsyncLevelOrderDepthTraverser()
    root_node = AsyncFileSystemNode(test_path)
    
    folder_count = 0
    async for depth, nodes in traverser.traverse_by_level(root_node, adapter, max_depth=2):
        for node in nodes:
            if node.path.is_dir():
                folder_count += 1
    
    print(f"Found {folder_count} folders")
    print(f"Skipped {len(policy.skipped_paths)} paths due to errors")
    for path in list(policy.skipped_paths)[:3]:
        print(f"  - {path}")
    
    print("\n" + "=" * 60)
    
    # Test 2: With FailFastPolicy (should fail on first error)
    print("\n2. Testing with FailFastPolicy:")
    strict_policy = FailFastPolicy()
    strict_adapter = ErrorHandlingAdapter(base_adapter, strict_policy)
    
    try:
        folder_count = 0
        async for depth, nodes in traverser.traverse_by_level(root_node, strict_adapter, max_depth=2):
            for node in nodes:
                if node.path.is_dir():
                    folder_count += 1
        print(f"Found {folder_count} folders (no errors encountered)")
    except PermissionError as e:
        print(f"Failed as expected on permission error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def test_unc_path():
    """Test with actual UNC path if available."""
    unc_path = Path(r"\\aktuldjr\j")
    
    if not unc_path.exists():
        print(f"\nUNC path {unc_path} not accessible, skipping UNC test")
        return
    
    print(f"\n\n3. Testing UNC path: {unc_path}")
    print("-" * 60)
    
    base_adapter = AsyncFileSystemAdapter(
        max_concurrent=10,
        batch_size=64,
        follow_symlinks=False
    )
    
    policy = ContinueOnErrorsPolicy(verbose=True)
    adapter = ErrorHandlingAdapter(base_adapter, policy)
    
    traverser = AsyncLevelOrderDepthTraverser()
    root_node = AsyncFileSystemNode(unc_path)
    
    folder_count = 0
    async for depth, nodes in traverser.traverse_by_level(root_node, adapter, max_depth=0):
        for node in nodes:
            if node.path.is_dir():
                folder_count += 1
                if folder_count <= 5:
                    print(f"  Found: {node.path.name}")
    
    print(f"\nTotal folders found: {folder_count}")
    print(f"Permission errors skipped: {len(policy.skipped_paths)}")


def main():
    print("=" * 60)
    print("Direct Test of PolicyDrivenErrorAdapter")
    print("=" * 60)
    
    asyncio.run(test_error_handling())
    asyncio.run(test_unc_path())
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    main()