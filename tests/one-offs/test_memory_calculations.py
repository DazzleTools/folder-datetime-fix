#!/usr/bin/env python3
"""Calculate actual memory usage for cache entries.

Related to Issue #17: Memory profiling for the new integer-based cache design.
Verifies that replacing enums with integers doesn't significantly impact memory.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('../..'))

from folder_datetime_fix.cache_wrapper import SmartCacheEntry, CacheCompleteness
from pathlib import Path

# Create a sample entry with correct parameters
entry = SmartCacheEntry(
    path=Path("C:/Users/Example/Documents/Projects/MyProject/src/components/subfolder"),
    computed_mtime=1234567890,
    completeness=CacheCompleteness.COMPLETE,
    actual_depth=5,
    has_subdirs=True,
    file_count=10,
    computation_time=0.001
)

# Calculate sizes
print("Memory Usage Analysis")
print("=" * 50)
print(f"Path string: {len(str(entry.path))} bytes")
print(f"SmartCacheEntry size: {sys.getsizeof(entry)} bytes")
print(f"Path object size: {sys.getsizeof(entry.path)} bytes")
print(f"mtime size: {sys.getsizeof(entry.computed_mtime)} bytes")
print(f"completeness size: {sys.getsizeof(entry.completeness)} bytes")

# With __slots__ optimization (if we had it)
class OptimizedEntry:
    __slots__ = ['path', 'mtime', 'completeness']
    def __init__(self, path, mtime, completeness):
        self.path = path
        self.mtime = mtime
        self.completeness = completeness

opt_entry = OptimizedEntry(
    path=str(entry.path),  # Store as string
    mtime=entry.computed_mtime,
    completeness=entry.completeness.value  # Store as int
)

print(f"\nWith __slots__ optimization: {sys.getsizeof(opt_entry)} bytes")

# Calculate for different folder counts
print("\nMemory Projections:")
print("-" * 50)

# Assume ~200 bytes per entry total (conservative)
bytes_per_entry = 200

for count in [1000, 10_000, 50_000, 100_000, 500_000, 1_000_000]:
    memory_mb = (count * bytes_per_entry) / (1024 * 1024)
    print(f"{count:>10,} folders: {memory_mb:>8.1f} MB")

print("\nSystem Memory Percentages (16GB system):")
print("-" * 50)
system_memory_mb = 16 * 1024  # 16GB in MB

for percent in [0.1, 0.5, 1.0, 2.0]:
    threshold_mb = system_memory_mb * (percent / 100)
    max_folders = int((threshold_mb * 1024 * 1024) / bytes_per_entry)
    print(f"{percent:>4.1f}% ({threshold_mb:>6.0f} MB): {max_folders:>10,} folders")

print("\nRecommended Thresholds:")
print("-" * 50)
print("Network paths: 50,000 folders (~10MB)")
print("Local paths: 500,000 folders (~100MB)")
print("With 1% system memory target: ~800,000 folders")