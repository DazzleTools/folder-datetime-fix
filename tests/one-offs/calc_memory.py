#!/usr/bin/env python3
"""Quick memory calculation."""

import sys
import psutil
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TestEntry:
    """Simulate cache entry."""
    path: Path
    mtime: float
    depth: int
    has_subdirs: bool
    file_count: int
    comp_time: float

# Create sample entry
entry = TestEntry(
    path=Path("C:/Users/Example/Documents/Projects/MyProject/src/components"),
    mtime=1234567890.123456,
    depth=5,
    has_subdirs=True,
    file_count=10,
    comp_time=0.001
)

# Calculate sizes
entry_size = sys.getsizeof(entry)
path_size = sys.getsizeof(entry.path)
dict_overhead = 300  # Approximate dict storage overhead

total_per_entry = entry_size + dict_overhead

print("Memory Usage Analysis")
print("=" * 50)
print(f"Entry object: {entry_size} bytes")
print(f"Path object: {path_size} bytes")
print(f"Est. total per cache entry: {total_per_entry} bytes")

print("\nMemory Projections:")
print("-" * 50)
for count in [10_000, 50_000, 100_000, 500_000, 1_000_000]:
    memory_mb = (count * total_per_entry) / (1024 * 1024)
    print(f"{count:>10,} folders: {memory_mb:>8.1f} MB")

# Get system memory
try:
    system_memory_gb = psutil.virtual_memory().total / (1024**3)
    print(f"\nSystem Memory: {system_memory_gb:.1f} GB")
    
    print("\nMemory Thresholds (% of system RAM):")
    print("-" * 50)
    for percent in [0.5, 1.0, 2.0]:
        threshold_mb = (system_memory_gb * 1024) * (percent / 100)
        max_folders = int((threshold_mb * 1024 * 1024) / total_per_entry)
        print(f"{percent:>4.1f}% ({threshold_mb:>6.0f} MB): {max_folders:>12,} folders")
except:
    print("\n(Could not detect system memory)")

print("\nRECOMMENDED THRESHOLDS:")
print("-" * 50)
print("Conservative (0.5% RAM):")
print("  Network: 100,000 folders")
print("  Local: 500,000 folders")
print("\nModerate (1% RAM):")
print("  Network: 200,000 folders")
print("  Local: 1,000,000 folders")
print("\nCurrent implementation:")
print("  Network: 500 folders (TOO LOW!)")
print("  Local: 10,000 folders (TOO LOW!)")