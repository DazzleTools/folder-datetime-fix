#!/usr/bin/env python3
"""Test os.walk filtering behavior."""

import os
from pathlib import Path
import tempfile
import shutil

# Create test structure
td = tempfile.mkdtemp()
base = Path(td)
print(f"Test dir: {base}")

# Create structure
(base / "normal").mkdir()
(base / "normal" / "level1").mkdir()
(base / "__pycache__").mkdir()
(base / "__pycache__" / "deep1").mkdir()
(base / "__pycache__" / "deep1" / "deep2").mkdir()

print("\n=== Walking WITHOUT filtering ===")
for root, dirs, files in os.walk(base, topdown=True):
    rel_path = Path(root).relative_to(base)
    depth = len(rel_path.parts) if str(rel_path) != '.' else 0
    print(f"Depth {depth}: {rel_path}")

print("\n=== Walking WITH filtering (modifying dirs list) ===")
max_depth = 0
for root, dirs, files in os.walk(base, topdown=True):
    # Filter BEFORE processing
    if '__pycache__' in dirs:
        dirs.remove('__pycache__')
        print(f"  Filtered __pycache__ from {Path(root).relative_to(base)}")
    
    rel_path = Path(root).relative_to(base)
    depth = len(rel_path.parts) if str(rel_path) != '.' else 0
    print(f"Depth {depth}: {rel_path}")
    if depth > max_depth:
        max_depth = depth

print(f"\nMax depth with filtering: {max_depth}")

# Clean up
shutil.rmtree(td)