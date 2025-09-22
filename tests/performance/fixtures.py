"""
Test fixtures for performance benchmarks.
"""

import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import random


@dataclass
class TestTreeConfig:
    """Configuration for test tree generation."""
    depth: int = 3
    width: int = 3
    files_per_folder: int = 3
    file_size: int = 100  # bytes
    include_system_files: bool = False
    random_timestamps: bool = True
    seed: Optional[int] = None


def create_test_tree(
    base_path: Optional[Path] = None,
    config: Optional[TestTreeConfig] = None
) -> Path:
    """
    Create a test directory tree for benchmarking.
    
    Args:
        base_path: Base path for the tree (temp dir if None)
        config: Configuration for tree generation
        
    Returns:
        Path to the created tree
    """
    if config is None:
        config = TestTreeConfig()
    
    # Set random seed for reproducibility
    if config.seed is not None:
        random.seed(config.seed)
    
    # Create base directory
    if base_path is None:
        base_path = Path(tempfile.mkdtemp(prefix='perf_test_'))
    else:
        if base_path.exists():
            shutil.rmtree(base_path)
        base_path.mkdir(parents=True)
    
    # Statistics
    total_folders = 0
    total_files = 0
    
    def create_level(path: Path, current_depth: int) -> tuple:
        """Recursively create tree structure."""
        nonlocal total_folders, total_files
        
        if current_depth >= config.depth:
            return total_folders, total_files
        
        # Create files at this level
        for i in range(config.files_per_folder):
            file_path = path / f"file_{current_depth}_{i}.txt"
            file_path.write_text("x" * config.file_size)
            total_files += 1
            
            # Set random timestamp if configured
            if config.random_timestamps:
                random_days = random.randint(1, 365)
                new_time = datetime.now() - timedelta(days=random_days)
                timestamp = new_time.timestamp()
                import os
                os.utime(file_path, (timestamp, timestamp))
        
        # Add system files if configured
        if config.include_system_files and random.random() > 0.5:
            thumbs = path / "Thumbs.db"
            thumbs.write_bytes(b"THUMBS")
            total_files += 1
            # System files get recent timestamps
            recent_time = datetime.now() - timedelta(hours=1)
            timestamp = recent_time.timestamp()
            import os
            os.utime(thumbs, (timestamp, timestamp))
        
        # Create subdirectories
        for i in range(config.width):
            subdir = path / f"folder_{current_depth}_{i}"
            subdir.mkdir(exist_ok=True)
            total_folders += 1
            
            # Set random timestamp for folder
            if config.random_timestamps:
                random_days = random.randint(1, 365)
                new_time = datetime.now() - timedelta(days=random_days)
                timestamp = new_time.timestamp()
                import os
                os.utime(subdir, (timestamp, timestamp))
            
            # Recurse
            create_level(subdir, current_depth + 1)
        
        return total_folders, total_files
    
    # Start creation
    total_folders, total_files = create_level(base_path, 0)
    
    # Add root to folder count
    total_folders += 1
    
    # Create a wrapper class for the path with statistics
    class TestTree:
        """Wrapper for test tree path with statistics."""
        def __init__(self, path, folders, files, config):
            self.path = path
            self.total_folders = folders
            self.total_files = files
            self.config = config
        
        def __str__(self):
            return str(self.path)
        
        def __fspath__(self):
            return str(self.path)
        
        # Delegate common Path methods
        def exists(self):
            return self.path.exists()
        
        def __truediv__(self, other):
            return self.path / other
    
    # Return wrapper
    result = TestTree(base_path, total_folders, total_files, config)
    return result


def cleanup_test_tree(path):
    """Clean up a test tree."""
    # Handle both Path and TestTree wrapper
    if hasattr(path, 'path'):
        actual_path = path.path
    else:
        actual_path = path
    
    if actual_path.exists() and str(actual_path).startswith(tempfile.gettempdir()):
        shutil.rmtree(actual_path, ignore_errors=True)


def generate_test_trees(configs: list) -> list:
    """
    Generate multiple test trees with different configurations.
    
    Args:
        configs: List of TestTreeConfig objects
        
    Returns:
        List of created tree paths
    """
    trees = []
    for config in configs:
        tree = create_test_tree(config=config)
        trees.append(tree)
    return trees


# Predefined configurations for common test scenarios
SMALL_TREE = TestTreeConfig(depth=2, width=2, files_per_folder=2)
MEDIUM_TREE = TestTreeConfig(depth=3, width=3, files_per_folder=3)
LARGE_TREE = TestTreeConfig(depth=4, width=4, files_per_folder=5)
DEEP_TREE = TestTreeConfig(depth=6, width=2, files_per_folder=2)
WIDE_TREE = TestTreeConfig(depth=2, width=10, files_per_folder=3)
SYSTEM_FILES_TREE = TestTreeConfig(depth=3, width=3, files_per_folder=3, include_system_files=True)