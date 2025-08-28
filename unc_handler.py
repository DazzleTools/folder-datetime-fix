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
        normalize_path,
        is_unc_path,
        is_network_drive,
        is_subst_drive,
        get_path_type,
        get_network_mappings,
    )
    UNCTOOLS_AVAILABLE = True
    import_error = None
except ImportError as e:
    UNCTOOLS_AVAILABLE = False
    import_error = str(e)
except Exception as e:
    # Catch any other errors during import
    UNCTOOLS_AVAILABLE = False
    import_error = f"Unexpected error: {str(e)}"

# Provide fallback implementations if unctools not available
if not UNCTOOLS_AVAILABLE:
    def is_unc_path(path: str) -> bool:
        """Basic check for UNC path format."""
        path_str = str(path)
        return path_str.startswith('\\\\') or path_str.startswith('//')
    
    def normalize_path(path: str) -> Path:
        """Basic path normalization without unctools."""
        path_str = str(path)
        if path_str.startswith('\\\\') or path_str.startswith('//'):
            # Keep UNC path as-is
            return Path(path)
        return Path(path).resolve()


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
        
        Args:
            path: Path to normalize (can be UNC, network drive, or local)
        
        Returns:
            Normalized Path object
        """
        if not self.unctools_available:
            # Basic normalization - preserve UNC paths
            path_str = str(path)
            if path_str.startswith('\\\\') or path_str.startswith('//'):
                # Keep UNC path as-is, don't resolve
                return Path(path)
            return Path(path).resolve()
        
        try:
            # Use unctools for advanced normalization
            normalized = normalize_path(path)
            return Path(normalized)
        except Exception as e:
            if self.verbose:
                print(f"UNCtools normalization failed, using basic: {e}")
            return Path(path).resolve()
    
    def get_path_info(self, path: str) -> dict:
        """
        Get detailed information about a path.
        
        Args:
            path: Path to analyze
        
        Returns:
            Dictionary with path information
        """
        path_obj = Path(path)
        info = {
            'original': str(path),
            'resolved': str(path_obj.resolve()),
            'exists': path_obj.exists(),
            'is_dir': path_obj.is_dir() if path_obj.exists() else False,
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
                info['type'] = get_path_type(path_str)
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