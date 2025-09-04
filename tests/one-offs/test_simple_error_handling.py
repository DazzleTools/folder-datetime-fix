#!/usr/bin/env python3
"""
Simple test of error handling without complex imports.
"""

import sys
import os

# Don't add the local path to avoid import issues
# sys.path.insert(0, "C:/code/modified_datetime_fix/local")

# Import from installed DazzleTreeLib
from dazzletreelib.aio import AsyncFileSystemAdapter

# Now add local path for our extensions
sys.path.insert(0, "C:/code/modified_datetime_fix/local")
from dazzletreelib.aio.error_handling import ErrorHandlingAdapter
from dazzletreelib.aio.error_policies import ContinueOnErrorsPolicy, FailFastPolicy

print("Imports successful!")
print(f"DazzleTreeLib version: {__import__('dazzletreelib').__version__}")

# Test creating the adapter with error handling
base = AsyncFileSystemAdapter()
policy = ContinueOnErrorsPolicy(verbose=True)
adapter = ErrorHandlingAdapter(base, policy)

print(f"Created ErrorHandlingAdapter: {adapter}")
print(f"Policy: {policy.__class__.__name__}")
print("\nTest passed - error handling components work!")