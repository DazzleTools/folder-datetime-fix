#!/usr/bin/env python3
"""
UNC path handler for network drive support.

This module integrates UNCtools to provide robust handling of UNC paths,
network drives, and substituted drives for the folder datetime fix tool.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List

# Try to import unctools if available
try:
    import unctools
    from unctools import (
        convert_to_local,
        convert_to_unc,
        is_unc_path,
        is_network_drive,
        is_subst_drive,
        classify_path_origin,
        get_network_mappings,
    )
    # NOTE: unctools no longer exports `normalize_path` -- it was removed in the
    # 0.2.0 "probe-not-mutate" surgery. unctools (L0) now only probes/classifies/
    # converts path IDENTITY; path NORMALIZATION moved DOWN to dazzle-filekit
    # (L1), imported separately below. We delegate to it rather than re-rolling.
    UNCTOOLS_AVAILABLE = True
    import_error = None
except ImportError as e:
    UNCTOOLS_AVAILABLE = False
    import_error = str(e)
except Exception as e:
    # Catch any other errors during import
    UNCTOOLS_AVAILABLE = False
    import_error = f"Unexpected error: {str(e)}"

# Path normalization is owned by dazzle-filekit (L1) since the unctools 0.2.0
# probe-not-mutate split. It is a HARD requirement -- normalization is core and
# cross-platform, so we delegate to it unconditionally (no fallback to re-roll).
from dazzle_filekit import normalize_cross_platform_path

# Fallback UNC-format check only when unctools is unavailable.
if not UNCTOOLS_AVAILABLE:
    def is_unc_path(path: str) -> bool:
        """Basic check for UNC path format."""
        path_str = str(path)
        return path_str.startswith('\\\\') or path_str.startswith('//')


class UNCHandler:
    """Handler for UNC paths and network drives."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the UNC handler.
        
        Args:
            verbose: If True, print diagnostic information
        """
        self.verbose = verbose
        self.unctools_available = UNCTOOLS_AVAILABLE
        self._mappings = None
        
        if self.unctools_available and self.verbose:
            print("UNCtools is available for enhanced network path support")
        elif self.verbose:
            print("UNCtools not found - using basic path handling")
            print("Install with: pip install unctools")
    
    def get_network_mappings(self) -> dict:
        """
        Get current network drive mappings.
        
        Returns:
            Dictionary mapping UNC paths to drive letters
        """
        if not self.unctools_available:
            return {}
        
        if self._mappings is None:
            try:
                self._mappings = get_network_mappings()
            except Exception as e:
                if self.verbose:
                    print(f"Could not get network mappings: {e}")
                self._mappings = {}
        
        return self._mappings
    
    def normalize_path(self, path: str) -> Path:
        """
        Normalize a path, handling UNC paths and network drives.

        Delegates to dazzle-filekit's ``normalize_cross_platform_path`` -- the
        canonical home for path normalization since unctools' 0.2.0
        probe-not-mutate split. Its default ``resolve=False`` is UNC-safe: it
        normalizes separators but does NOT resolve a UNC path down to a drive
        letter, which would break the share.

        Args:
            path: Path to normalize (can be UNC, network drive, or local)

        Returns:
            Normalized Path object
        """
        return normalize_cross_platform_path(path)
    
    def get_path_info(self, path: str) -> dict:
        """
        Get detailed information about a path.
        
        Args:
            path: Path to analyze
        
        Returns:
            Dictionary with path information
        """
        path_obj = Path(path)
        # Resolving or stat-ing a path can hit the filesystem -- and for a UNC
        # path, the NETWORK. An unreachable share raises OSError (e.g.
        # [WinError 64] "network name is no longer available"), notably on
        # Python 3.9 Windows where Path.resolve()/exists() do not swallow
        # network errors the way 3.10+ do. Degrade gracefully so path
        # inspection never crashes on a dead share.
        try:
            resolved = str(path_obj.resolve())
        except OSError:
            resolved = str(path_obj)
        try:
            exists = path_obj.exists()
        except OSError:
            exists = False
        try:
            is_dir = path_obj.is_dir() if exists else False
        except OSError:
            is_dir = False
        info = {
            'original': str(path),
            'resolved': resolved,
            'exists': exists,
            'is_dir': is_dir,
            'is_unc': False,
            'is_network': False,
            'is_subst': False,
            'type': 'local'
        }
        
        if self.unctools_available:
            try:
                path_str = str(path)
                info['is_unc'] = is_unc_path(path_str)
                info['is_network'] = is_network_drive(path_str)
                info['is_subst'] = is_subst_drive(path_str)
                info['type'] = classify_path_origin(path_str)
            except Exception as e:
                if self.verbose:
                    print(f"Could not get detailed path info: {e}")
        else:
            # Basic UNC detection
            path_str = str(path)
            info['is_unc'] = path_str.startswith('\\\\') or path_str.startswith('//')
        
        return info
    
    def convert_for_processing(self, path: str) -> Tuple[Path, bool]:
        """
        Convert a path to the best format for processing.
        
        For UNC paths, tries to convert to a mapped drive letter if available
        for better performance. Returns the path and whether it's a network path.
        
        Args:
            path: Path to convert
        
        Returns:
            Tuple of (converted_path, is_network)
        """
        path_str = str(path)
        
        # Detect ambiguous path that might be a shell-mangled UNC path
        # But DON'T auto-fix it as it could be a valid local path
        if path_str.startswith('\\') and not path_str.startswith('\\\\'):
            if self.verbose:
                print(f"WARNING: Path starts with single backslash: {path_str}")
                print("If this is a UNC path, use forward slashes: //server/share")
                print("Or escape properly in shell: \\\\\\\\server\\\\share")
        
        path_obj = self.normalize_path(path_str)
        is_network = False
        
        if not self.unctools_available:
            # Basic check for UNC
            path_str = str(path_obj)
            is_network = path_str.startswith('\\\\') or path_str.startswith('//')
            return path_obj, is_network
        
        try:
            path_str = str(path_obj)
            
            # Check if it's a UNC path
            if is_unc_path(path_str):
                is_network = True
                
                # Try to convert to local mapped drive for better performance
                try:
                    local_path = convert_to_local(path_str)
                    if local_path and local_path != path_str:
                        if self.verbose:
                            print(f"Converted UNC to local: {path_str} -> {local_path}")
                        return Path(local_path), is_network
                except Exception:
                    pass  # Keep using UNC path
            
            # Check if it's already a network drive
            elif is_network_drive(path_str) or is_subst_drive(path_str):
                is_network = True
        
        except Exception as e:
            if self.verbose:
                print(f"Path conversion check failed: {e}")
        
        return path_obj, is_network
    
    def prepare_path_list(self, paths: List[str]) -> List[Tuple[Path, dict]]:
        """
        Prepare a list of paths for processing.
        
        Args:
            paths: List of paths to prepare
        
        Returns:
            List of tuples (path_object, path_info)
        """
        prepared = []
        
        for path in paths:
            path_obj, is_network = self.convert_for_processing(path)
            info = self.get_path_info(path)
            info['converted_path'] = str(path_obj)
            info['is_network_for_processing'] = is_network
            
            prepared.append((path_obj, info))
        
        return prepared
    
    def handle_network_error(self, error: Exception, path: Path) -> bool:
        """
        Handle network-related errors.
        
        Args:
            error: The exception that occurred
            path: Path that caused the error
        
        Returns:
            True if error was handled and operation should retry, False otherwise
        """
        error_str = str(error).lower()
        
        # Common network error patterns
        network_errors = [
            'network path not found',
            'network location cannot be reached',
            'network name cannot be found',
            'access is denied',
            'the specified network name is no longer available',
        ]
        
        is_network_error = any(err in error_str for err in network_errors)
        
        if is_network_error:
            if self.verbose:
                print(f"Network error for {path}: {error}")
            
            # Check if path is UNC and we can try alternative
            if self.unctools_available:
                try:
                    path_str = str(path)
                    if is_unc_path(path_str):
                        # Try to get UNC from mapped drive or vice versa
                        alt_path = convert_to_unc(path_str) if not is_unc_path(path_str) else convert_to_local(path_str)
                        if alt_path and alt_path != path_str:
                            if self.verbose:
                                print(f"Trying alternative path: {alt_path}")
                            return True
                except Exception:
                    pass
        
        return False


def get_unc_handler(verbose: bool = False) -> UNCHandler:
    """
    Get a UNC handler instance.
    
    Args:
        verbose: If True, print diagnostic information
    
    Returns:
        UNCHandler instance
    """
    return UNCHandler(verbose=verbose)