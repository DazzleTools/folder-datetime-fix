"""
Advanced exclusion filter with glob pattern support and smart file/folder detection.
"""

import fnmatch
import re
from enum import Enum
from pathlib import Path
from typing import Set, List, Optional, Union, Tuple
from .system_files import SYSTEM_GENERATED_FILES, SYSTEM_GENERATED_FOLDERS, is_system_generated


class ExclusionMode(Enum):
    """Base exclusion modes for system files."""
    DEFAULT = 'default'    # Skip all system files/folders
    NONE = 'none'         # Include everything
    FILES = 'files'       # Skip only system files
    FOLDERS = 'folders'   # Skip only system folders


class ExclusionFilter:
    """
    Handles file/folder exclusion with glob pattern support and smart type detection.
    
    Precedence (highest to lowest):
    1. Include patterns (always win)
    2. Exclude patterns
    3. Mode-based filtering (system files)
    """
    
    def __init__(self,
                 mode: ExclusionMode = ExclusionMode.DEFAULT,
                 exclude_patterns: Optional[List[str]] = None,
                 include_patterns: Optional[List[str]] = None):
        """
        Initialize exclusion filter.
        
        Args:
            mode: Base exclusion mode for system files
            exclude_patterns: Glob patterns to exclude
            include_patterns: Glob patterns to include (override excludes)
        """
        self.mode = mode
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
        
        # Create sets for known file/folder types for smart matching
        self._known_files = {f.lower() for f in SYSTEM_GENERATED_FILES 
                            if not f.startswith('*') and not f.endswith('*')}
        self._known_folders = {f.lower() for f in SYSTEM_GENERATED_FOLDERS}
        
        # Cache for pattern matching performance
        self._pattern_cache = {}
        self._compile_patterns()
    
    def should_exclude(self, path: Union[str, Path], is_dir: Optional[bool] = None) -> bool:
        """
        Determine if path should be excluded.
        
        Args:
            path: Path to check (can be relative or absolute)
            is_dir: Whether path is directory. If None, uses smart detection.
        
        Returns:
            True if path should be excluded, False otherwise
        """
        if isinstance(path, str):
            path = Path(path)
        
        # Smart detection of file vs folder if not specified
        if is_dir is None:
            is_dir = self._smart_is_dir(path)
        
        # Normalize path for consistent matching
        path_str = str(path).replace('\\', '/')
        name = path.name
        
        # Priority 1: Include patterns (highest priority)
        if self._matches_includes(path_str, name):
            return False
        
        # Priority 2: Exclude patterns
        matched, should_exclude = self._check_exclude_patterns(path_str, name, is_dir)
        if matched:
            return should_exclude
        
        # Priority 3: Mode-based filtering (only if no patterns matched)
        return self._apply_mode_filter(name, is_dir)
    
    def _smart_is_dir(self, path: Path) -> bool:
        """
        Smart detection of whether path is a directory.
        
        Uses known patterns and filesystem checks.
        """
        # First try filesystem check if path exists
        if path.exists():
            return path.is_dir()
        
        name_lower = path.name.lower()
        
        # Check against known folder patterns
        if name_lower in self._known_folders:
            return True
        
        # Check against known file patterns
        if name_lower in self._known_files:
            return False
        
        # Check for file extensions (indicates file)
        if '.' in path.name and not path.name.startswith('.'):
            # Has extension, likely a file
            return False
        
        # Default assumption for unknown items
        # (folders are more commonly excluded by name only)
        return False
    
    def _apply_mode_filter(self, name: str, is_dir: bool) -> bool:
        """Apply mode-based filtering rules."""
        if self.mode == ExclusionMode.NONE:
            return False
        elif self.mode == ExclusionMode.DEFAULT:
            return is_system_generated(name)
        elif self.mode == ExclusionMode.FILES and not is_dir:
            return is_system_generated(name)
        elif self.mode == ExclusionMode.FOLDERS and is_dir:
            return is_system_generated(name)
        
        return False
    
    def _compile_patterns(self):
        """Pre-process patterns for efficient matching."""
        # Separate patterns by type for optimized matching
        self.simple_excludes = set()
        self.glob_excludes = []
        self.recursive_excludes = []
        self.dir_excludes = set()  # Patterns ending with /
        
        self.simple_includes = set()
        self.glob_includes = []
        self.recursive_includes = []
        self.dir_includes = set()  # Patterns ending with /
        
        # Process exclude patterns
        for pattern in self.exclude_patterns:
            pattern = pattern.strip()
            if not pattern:
                continue
            
            # Directory marker pattern (ends with /)
            if pattern.endswith('/'):
                self.dir_excludes.add(pattern[:-1].lower())
            elif '**' in pattern:
                # Recursive pattern
                regex = self._glob_to_regex(pattern)
                self.recursive_excludes.append((pattern, re.compile(regex, re.IGNORECASE)))
            elif any(c in pattern for c in '*?['):
                # Glob pattern
                self.glob_excludes.append(pattern)
            else:
                # Simple string match
                self.simple_excludes.add(pattern.lower())
        
        # Process include patterns
        for pattern in self.include_patterns:
            pattern = pattern.strip()
            if not pattern:
                continue
            
            # Directory marker pattern (ends with /)
            if pattern.endswith('/'):
                self.dir_includes.add(pattern[:-1].lower())
            elif '**' in pattern:
                # Recursive pattern
                regex = self._glob_to_regex(pattern)
                self.recursive_includes.append((pattern, re.compile(regex, re.IGNORECASE)))
            elif any(c in pattern for c in '*?['):
                # Glob pattern
                self.glob_includes.append(pattern)
            else:
                # Simple string match
                self.simple_includes.add(pattern.lower())
    
    def _glob_to_regex(self, pattern: str) -> str:
        """Convert glob pattern with ** to regex."""
        # Normalize path separators
        pattern = pattern.replace('\\', '/')
        original_pattern = pattern
        
        # Escape special regex characters except our glob markers
        parts = []
        i = 0
        while i < len(pattern):
            if i < len(pattern) - 1 and pattern[i:i+2] == '**':
                parts.append('**')
                i += 2
            elif pattern[i] == '*':
                parts.append('*')
                i += 1
            elif pattern[i] == '?':
                parts.append('?')
                i += 1
            else:
                # Regular character, escape if needed
                char = pattern[i]
                if char in r'\.+^${}()|':
                    parts.append('\\' + char)
                elif char == '[':
                    parts.append('\\[')
                elif char == ']':
                    parts.append('\\]')
                else:
                    parts.append(char)
                i += 1
        
        # Convert glob patterns to regex
        regex = ''.join(parts)
        
        # Handle anchoring and ** patterns
        if original_pattern.startswith('**/'):
            # Pattern like **/node_modules should match at any depth
            # Remove the **/ from the beginning
            regex = regex[3:]  # Remove \*\*/ (which is still **)
            regex = regex.replace('**', '.*')  # Convert any remaining **
            regex = regex.replace('*', '[^/]*')  # Convert single *
            regex = regex.replace('?', '[^/]')   # Convert ?
            # Add anchor for matching at any depth
            regex = '(^|.*/|^.*/)' + regex
        elif original_pattern.endswith('/**'):
            # Pattern like logs/** matches everything under logs/
            regex = regex[:-3]  # Remove /**
            regex = regex.replace('**', '.*')
            regex = regex.replace('*', '[^/]*')
            regex = regex.replace('?', '[^/]')
            regex = '^' + regex + '/.*'
        elif '**' in regex:
            # Pattern with ** in the middle like test/**/file.txt
            # First handle ** patterns before converting single *
            regex = regex.replace('**/', '##DOUBLESTAR_SLASH##')
            regex = regex.replace('/**', '##SLASH_DOUBLESTAR##')
            regex = regex.replace('**', '##DOUBLESTAR##')
            
            # Now convert single * and ?
            regex = regex.replace('*', '[^/]*')
            regex = regex.replace('?', '[^/]')
            
            # Now replace the ** placeholders with actual regex
            regex = regex.replace('##DOUBLESTAR_SLASH##', '(.*/)?')
            regex = regex.replace('##SLASH_DOUBLESTAR##', '(/.*)?')
            regex = regex.replace('##DOUBLESTAR##', '.*')
            
            if '/' in original_pattern:
                regex = '^' + regex
            else:
                regex = '(^|/)' + regex
        else:
            # Simple patterns without **
            regex = regex.replace('*', '[^/]*')
            regex = regex.replace('?', '[^/]')
            if '/' in original_pattern:
                regex = '^' + regex
            else:
                regex = '(^|/)' + regex
        
        regex = regex + '$'
        
        return regex
    
    def _check_exclude_patterns(self, path_str: str, name: str, is_dir: bool) -> tuple[bool, bool]:
        """Check if path matches exclude patterns.
        
        Returns:
            (matched, should_exclude) - matched indicates if any pattern was checked,
            should_exclude indicates if the item should be excluded.
        """
        path_lower = path_str.lower()
        name_lower = name.lower()
        
        # Check directory-specific excludes (patterns ending with /)
        if name_lower in self.dir_excludes:
            # Pattern matched - return whether it should be excluded
            return (True, is_dir)
        
        # Check simple excludes
        if name_lower in self.simple_excludes:
            # Smart check: if this is a known folder pattern, only match if is_dir
            if name_lower in self._known_folders:
                return (True, is_dir)
            # If known file pattern, only match if not is_dir
            elif name_lower in self._known_files:
                return (True, not is_dir)
            # Otherwise match regardless
            return (True, True)
        
        # Check glob patterns
        for pattern in self.glob_excludes:
            if '/' in pattern:
                # Full path pattern
                if fnmatch.fnmatch(path_lower, pattern.lower()):
                    return (True, True)
            else:
                # Name-only pattern
                if fnmatch.fnmatch(name_lower, pattern.lower()):
                    return (True, True)
        
        # Check recursive patterns
        for pattern, regex in self.recursive_excludes:
            if regex.search(path_lower):
                return (True, True)
        
        # No patterns matched
        return (False, False)
    
    def _matches_includes(self, path_str: str, name: str) -> bool:
        """Check if path matches include patterns."""
        path_lower = path_str.lower()
        name_lower = name.lower()
        
        # Check directory-specific includes
        if name_lower in self.dir_includes:
            return True
        
        # Check simple includes
        if name_lower in self.simple_includes:
            return True
        
        # Check glob patterns
        for pattern in self.glob_includes:
            if '/' in pattern:
                # Full path pattern
                if fnmatch.fnmatch(path_lower, pattern.lower()):
                    return True
            else:
                # Name-only pattern
                if fnmatch.fnmatch(name_lower, pattern.lower()):
                    return True
        
        # Check recursive patterns
        for pattern, regex in self.recursive_includes:
            if regex.search(path_lower):
                return True
        
        return False
    
    @classmethod
    def from_args(cls, mode: str = 'default',
                  exclude: Optional[str] = None,
                  include: Optional[str] = None) -> 'ExclusionFilter':
        """
        Create filter from CLI arguments.
        
        Args:
            mode: Exclusion mode string
            exclude: Comma-separated exclude patterns
            include: Comma-separated include patterns
        
        Returns:
            Configured ExclusionFilter instance
        """
        # Parse mode
        try:
            mode_enum = ExclusionMode(mode)
        except ValueError:
            mode_enum = ExclusionMode.DEFAULT
        
        # Parse patterns (handle escaped commas)
        exclude_patterns = []
        if exclude:
            # Simple split for now, can enhance with escape handling later
            exclude_patterns = [p.strip() for p in exclude.split(',') if p.strip()]
        
        include_patterns = []
        if include:
            include_patterns = [p.strip() for p in include.split(',') if p.strip()]
        
        return cls(mode_enum, exclude_patterns, include_patterns)
    
    @classmethod
    def from_legacy(cls, skip_generated: bool = True) -> 'ExclusionFilter':
        """
        Create filter from legacy skip_generated flag.
        
        Args:
            skip_generated: If True, skip system files (default behavior)
        
        Returns:
            ExclusionFilter with appropriate mode
        """
        if skip_generated:
            return cls(ExclusionMode.DEFAULT)
        else:
            return cls(ExclusionMode.NONE)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"ExclusionFilter(mode={self.mode.value}, "
                f"excludes={len(self.exclude_patterns)}, "
                f"includes={len(self.include_patterns)})")