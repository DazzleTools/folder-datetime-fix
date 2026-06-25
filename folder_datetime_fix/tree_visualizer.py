#!/usr/bin/env python3
"""
Tree visualization tool for debugging folder structures and analysis strategies.
Provides both console output and optional graphical rendering.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict

from .console_safe import icon, stream_can_encode

# Try to import optional dependencies for graphical output
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


class TreeVisualizer:
    """Visualize folder tree structures for debugging."""
    
    # Box drawing characters for console output
    TREE_CHARS = {
        'branch': '├── ',
        'last': '└── ',
        'pipe': '│   ',
        'space': '    '
    }
    
    # ASCII fallback for systems without Unicode support
    TREE_CHARS_ASCII = {
        'branch': '+-- ',
        'last': '`-- ',
        'pipe': '|   ',
        'space': '    '
    }
    
    def __init__(self, use_unicode: bool = True, show_timestamps: bool = True,
                 show_sizes: bool = False, show_depth: bool = True):
        """
        Initialize visualizer.
        
        Args:
            use_unicode: Use Unicode box drawing characters
            show_timestamps: Show modification times
            show_sizes: Show folder sizes (file count)
            show_depth: Show depth numbers
        """
        # Use Unicode box chars only when requested AND the console can encode
        # them -- a cp1252 Windows console would otherwise crash on output.
        if use_unicode and stream_can_encode(self.TREE_CHARS['branch']):
            self.chars = self.TREE_CHARS
        else:
            self.chars = self.TREE_CHARS_ASCII
        self.show_timestamps = show_timestamps
        self.show_sizes = show_sizes
        self.show_depth = show_depth
        self.stats = {
            'total_folders': 0,
            'total_files': 0,
            'max_depth': 0,
            'folders_by_depth': defaultdict(int)
        }
    
    def visualize_path(self, path: Path, max_depth: Optional[int] = None,
                       skip_hidden: bool = True, skip_system: bool = True,
                       use_ascii: bool = False) -> str:
        """
        Create console visualization of folder tree.
        
        Args:
            path: Root path to visualize
            max_depth: Maximum depth to traverse
            skip_hidden: Skip hidden files/folders
            skip_system: Skip system-generated files/folders
            
        Returns:
            String representation of tree
        """
        path = Path(path).resolve()
        if not path.exists():
            return f"Error: Path {path} does not exist"
        
        output = []
        folder_icon = icon("📁", "[DIR]", force_ascii=use_ascii)
        output.append(f"{folder_icon} {path}")
        
        if self.show_timestamps:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            output[0] += f" [{mtime.strftime('%Y-%m-%d %H:%M:%S')}]"
        
        if self.show_depth:
            output[0] += " (depth: 0)"
        
        output.append("")
        
        # Reset stats
        self.stats = {
            'total_folders': 1,
            'total_files': 0,
            'max_depth': 0,
            'folders_by_depth': defaultdict(int)
        }
        self.stats['folders_by_depth'][0] = 1
        
        # Build tree
        self._build_tree(path, output, "", 0, max_depth, skip_hidden, skip_system, use_ascii)
        
        # Add statistics
        output.append("")
        output.append("=" * 50)
        output.append("STATISTICS")
        output.append("=" * 50)
        output.append(f"Total folders: {self.stats['total_folders']:,}")
        output.append(f"Total files: {self.stats['total_files']:,}")
        output.append(f"Maximum depth: {self.stats['max_depth']}")
        
        if self.stats['folders_by_depth']:
            output.append("\nFolders by depth:")
            for depth in sorted(self.stats['folders_by_depth'].keys()):
                count = self.stats['folders_by_depth'][depth]
                output.append(f"  Depth {depth}: {count:,} folders")
        
        return "\n".join(output)
    
    def _build_tree(self, path: Path, output: List[str], prefix: str,
                   depth: int, max_depth: Optional[int],
                   skip_hidden: bool, skip_system: bool, use_ascii: bool = False):
        """Recursively build tree representation."""
        if max_depth is not None and depth >= max_depth:
            return
        
        try:
            # Get entries
            entries = list(path.iterdir())
            
            # Filter entries
            if skip_hidden:
                entries = [e for e in entries if not e.name.startswith('.')]
            
            if skip_system:
                from .system_files import is_system_generated
                entries = [e for e in entries if not is_system_generated(e.name)]
            
            # Separate files and folders
            files = sorted([e for e in entries if e.is_file()])
            folders = sorted([e for e in entries if e.is_dir()])
            
            # Update stats
            self.stats['total_files'] += len(files)
            
            # Show files first (optional)
            for i, file in enumerate(files):
                is_last_file = (i == len(files) - 1) and len(folders) == 0
                char = self.chars['last'] if is_last_file else self.chars['branch']
                
                file_icon = icon("📄", "[FILE]", force_ascii=use_ascii)
                line = f"{prefix}{char}{file_icon} {file.name}"
                
                if self.show_timestamps:
                    try:
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        line += f" [{mtime.strftime('%Y-%m-%d %H:%M:%S')}]"
                    except:
                        line += " [error reading timestamp]"
                
                output.append(line)
            
            # Show folders
            for i, folder in enumerate(folders):
                is_last = i == len(folders) - 1
                char = self.chars['last'] if is_last else self.chars['branch']
                
                # Update stats
                self.stats['total_folders'] += 1
                self.stats['folders_by_depth'][depth + 1] += 1
                if depth + 1 > self.stats['max_depth']:
                    self.stats['max_depth'] = depth + 1
                
                # Build folder line
                folder_icon = icon("📁", "[DIR]", force_ascii=use_ascii)
                line = f"{prefix}{char}{folder_icon} {folder.name}"
                
                if self.show_timestamps:
                    try:
                        mtime = datetime.fromtimestamp(folder.stat().st_mtime)
                        line += f" [{mtime.strftime('%Y-%m-%d %H:%M:%S')}]"
                    except:
                        line += " [error]"
                
                if self.show_sizes:
                    try:
                        size = len(list(folder.iterdir()))
                        line += f" ({size} items)"
                    except:
                        line += " (?)"
                
                if self.show_depth:
                    line += f" (depth: {depth + 1})"
                
                output.append(line)
                
                # Recurse into subfolder
                next_prefix = prefix + (self.chars['space'] if is_last else self.chars['pipe'])
                self._build_tree(folder, output, next_prefix, depth + 1,
                               max_depth, skip_hidden, skip_system, use_ascii)
        
        except PermissionError:
            output.append(f"{prefix}[Permission Denied]")
        except Exception as e:
            output.append(f"{prefix}[Error: {e}]")
    
    def visualize_analysis_result(self, results: List[Tuple[Path, Optional[datetime]]],
                                  base_path: Optional[Path] = None) -> str:
        """
        Visualize results from analysis strategies.
        
        Args:
            results: List of (path, timestamp) tuples from analysis
            base_path: Optional base path for relative display
            
        Returns:
            Console visualization of results
        """
        if not results:
            return "No results to visualize"
        
        output = []
        output.append("ANALYSIS RESULTS VISUALIZATION")
        output.append("=" * 60)
        
        # Group by depth
        by_depth = defaultdict(list)
        
        for path, timestamp in results:
            if base_path:
                try:
                    rel_path = path.relative_to(base_path)
                    depth = len(rel_path.parts)
                except:
                    depth = 0
            else:
                depth = len(path.parts)
            
            by_depth[depth].append((path, timestamp))
        
        # Display by depth
        for depth in sorted(by_depth.keys()):
            output.append(f"\nDepth {depth}: ({len(by_depth[depth])} folders)")
            output.append("-" * 40)
            
            for path, timestamp in sorted(by_depth[depth]):
                # Create indentation
                indent = "  " * depth
                
                # Format path
                if base_path:
                    try:
                        display_path = path.relative_to(base_path)
                    except:
                        display_path = path
                else:
                    display_path = path.name if depth > 0 else path
                
                # Build line
                line = f"{indent}{icon('📁', '[DIR]')} {display_path}"
                
                if timestamp:
                    line += f" [{timestamp.strftime('%Y-%m-%d %H:%M:%S')}]"
                else:
                    line += " [No timestamp]"
                
                output.append(line)
        
        # Statistics
        output.append("")
        output.append("=" * 60)
        output.append("SUMMARY")
        output.append("=" * 60)
        output.append(f"Total folders: {len(results)}")
        
        with_timestamps = sum(1 for _, ts in results if ts is not None)
        without_timestamps = len(results) - with_timestamps
        
        output.append(f"With timestamps: {with_timestamps}")
        output.append(f"Without timestamps: {without_timestamps}")
        
        if with_timestamps > 0:
            timestamps = [ts for _, ts in results if ts is not None]
            newest = max(timestamps)
            oldest = min(timestamps)
            output.append(f"Newest: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
            output.append(f"Oldest: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(output)
    
    def export_graphviz(self, path: Path, output_file: str = "tree.gv",
                       max_depth: Optional[int] = None) -> Optional[str]:
        """
        Export tree as Graphviz DOT file.
        
        Args:
            path: Root path to visualize
            output_file: Output filename
            max_depth: Maximum depth to traverse
            
        Returns:
            Path to output file or None if graphviz not available
        """
        if not HAS_GRAPHVIZ:
            return None
        
        dot = graphviz.Digraph(comment='Folder Tree')
        dot.attr(rankdir='TB')
        dot.attr('node', shape='folder', style='filled', fillcolor='lightblue')
        
        path = Path(path).resolve()
        
        # Add root
        root_id = str(path)
        dot.node(root_id, path.name)
        
        # Build graph
        self._build_graph(dot, path, root_id, 0, max_depth)
        
        # Save
        dot.render(output_file, format='svg', cleanup=True)
        return f"{output_file}.svg"
    
    def _build_graph(self, dot, path: Path, parent_id: str,
                    depth: int, max_depth: Optional[int]):
        """Recursively build Graphviz graph."""
        if max_depth is not None and depth >= max_depth:
            return
        
        try:
            for entry in sorted(path.iterdir()):
                if entry.is_dir():
                    node_id = str(entry)
                    
                    # Color based on depth
                    colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lightgray']
                    color = colors[depth % len(colors)]
                    
                    dot.node(node_id, entry.name, fillcolor=color)
                    dot.edge(parent_id, node_id)
                    
                    # Recurse
                    self._build_graph(dot, entry, node_id, depth + 1, max_depth)
        except:
            pass


def print_tree(path: str, max_depth: int = 3, show_files: bool = True,
              skip_system: bool = True):
    """
    Convenience function to quickly visualize a tree.
    
    Args:
        path: Path to visualize
        max_depth: Maximum depth
        show_files: Include files in output
        skip_system: Skip system files/folders
    """
    visualizer = TreeVisualizer(show_timestamps=True, show_sizes=True)
    result = visualizer.visualize_path(Path(path), max_depth=max_depth,
                                      skip_system=skip_system)
    print(result)


if __name__ == '__main__':
    # Simple CLI interface
    if len(sys.argv) < 2:
        print("Usage: python tree_visualizer.py <path> [max_depth]")
        sys.exit(1)
    
    path = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print_tree(path, max_depth)