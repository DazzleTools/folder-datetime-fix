"""
Folder scanner module for depth-based directory traversal and timestamp collection.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple
from system_files import is_system_generated


class FolderScanner:
    """Scans folders and collects timestamp information based on depth and strategy."""
    
    def __init__(self, skip_generated: bool = False):
        """
        Initialize the scanner.
        
        Args:
            skip_generated: If True, exclude system-generated files from timestamp calculation
        """
        self.skip_generated = skip_generated
    
    def get_folders_at_depth(self, base_path: Path, depth: int) -> List[Path]:
        """
        Get all folders at a specific depth from the base path.
        
        Args:
            base_path: Starting directory
            depth: How many levels down to look (0 = base itself)
        
        Returns:
            List of folder paths at the specified depth
        """
        base_path = Path(base_path).resolve()
        
        if depth == 0:
            return [base_path] if base_path.is_dir() else []
        
        folders = []
        
        def _traverse(current_path: Path, current_depth: int):
            if current_depth == depth:
                if current_path.is_dir():
                    folders.append(current_path)
                return
            
            if current_depth < depth and current_path.is_dir():
                try:
                    for child in current_path.iterdir():
                        if child.is_dir():
                            _traverse(child, current_depth + 1)
                except PermissionError:
                    pass  # Skip folders we can't access
        
        _traverse(base_path, 0)
        return sorted(folders)
    
    def get_shallow_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Get the most recent timestamp from immediate children only.
        
        Args:
            folder_path: Directory to scan
        
        Returns:
            Most recent timestamp or None if no valid files
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        latest_time = None
        
        try:
            for item in folder_path.iterdir():
                # Skip if it's a directory
                if item.is_dir():
                    continue
                
                # Skip system-generated files if flag is set
                if self.skip_generated and is_system_generated(item.name):
                    continue
                
                try:
                    # Get modified time
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if latest_time is None or mtime > latest_time:
                        latest_time = mtime
                
                except (OSError, PermissionError):
                    continue  # Skip files we can't access
        
        except PermissionError:
            return None
        
        return latest_time
    
    def get_deep_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Get the most recent timestamp from entire subtree.
        
        Args:
            folder_path: Directory to scan recursively
        
        Returns:
            Most recent timestamp or None if no valid files
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        latest_time = None
        visited = set()  # Track visited paths to avoid circular references
        
        def _scan_recursive(current_path: Path):
            nonlocal latest_time
            
            # Avoid circular references (junctions/symlinks)
            real_path = current_path.resolve()
            if real_path in visited:
                return
            visited.add(real_path)
            
            try:
                for item in current_path.iterdir():
                    if item.is_dir():
                        # Recurse into subdirectories
                        _scan_recursive(item)
                    else:
                        # Skip system-generated files if flag is set
                        if self.skip_generated and is_system_generated(item.name):
                            continue
                        
                        try:
                            # Get modified time
                            mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            
                            if latest_time is None or mtime > latest_time:
                                latest_time = mtime
                        
                        except (OSError, PermissionError):
                            continue
            
            except PermissionError:
                pass  # Skip folders we can't access
        
        _scan_recursive(folder_path)
        return latest_time
    
    def get_smart_timestamp(self, folder_path: Path) -> Optional[datetime]:
        """
        Use heuristics to decide between shallow and deep scanning.
        
        Args:
            folder_path: Directory to scan
        
        Returns:
            Most recent timestamp using smart strategy
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.is_dir():
            return None
        
        # Check if folder has subdirectories
        has_subdirs = False
        try:
            for item in folder_path.iterdir():
                if item.is_dir():
                    has_subdirs = True
                    break
        except PermissionError:
            return None
        
        # If it has subdirectories, go deep; otherwise shallow
        if has_subdirs:
            return self.get_deep_timestamp(folder_path)
        else:
            return self.get_shallow_timestamp(folder_path)
    
    def scan_and_collect(self, base_path: Path, depths: List[int], 
                        strategy: str = 'shallow') -> List[Tuple[Path, Optional[datetime]]]:
        """
        Scan folders at specified depths and collect their timestamps.
        
        Args:
            base_path: Starting directory
            depths: List of depths to process
            strategy: 'shallow', 'deep', or 'smart'
        
        Returns:
            List of (folder_path, timestamp) tuples
        """
        results = []
        processed = set()  # Avoid processing same folder twice
        
        for depth in sorted(depths):
            folders = self.get_folders_at_depth(base_path, depth)
            
            for folder in folders:
                if folder in processed:
                    continue
                processed.add(folder)
                
                # Get timestamp based on strategy
                if strategy == 'shallow':
                    timestamp = self.get_shallow_timestamp(folder)
                    results.append((folder, timestamp))
                elif strategy == 'deep':
                    # For deep strategy, we need to fix ALL subfolders too
                    timestamp = self.get_deep_timestamp(folder)
                    results.append((folder, timestamp))
                    
                    # When using deep strategy, also process all subfolders
                    # This ensures intermediate folders get fixed
                    for root, dirs, _ in os.walk(folder):
                        root_path = Path(root)
                        if root_path != folder and root_path not in processed:
                            # Each subfolder gets the timestamp of its own subtree
                            subfolder_timestamp = self.get_deep_timestamp(root_path)
                            results.append((root_path, subfolder_timestamp))
                            processed.add(root_path)
                            
                elif strategy == 'smart':
                    timestamp = self.get_smart_timestamp(folder)
                    results.append((folder, timestamp))
                    
                    # For smart strategy with subdirs, also process them
                    if any(p.is_dir() for p in folder.iterdir()):
                        for root, dirs, _ in os.walk(folder):
                            root_path = Path(root)
                            if root_path != folder and root_path not in processed:
                                subfolder_timestamp = self.get_smart_timestamp(root_path)
                                results.append((root_path, subfolder_timestamp))
                                processed.add(root_path)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")
        
        return results