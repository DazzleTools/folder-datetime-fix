#!/usr/bin/env python3
"""
Delete Windows NUL device file that gets accidentally created.

This script handles the special case where a file named "nul" gets created
in a directory. On Windows, NUL is a reserved device name (like CON, PRN, AUX)
and such files can be difficult to delete through normal means.

This typically happens when a script accidentally redirects output to "nul"
instead of "NUL" or "/dev/null".

Usage:
    python delete_nul.py [path_to_nul_file]
    
    If no path is provided, looks for 'nul' in the current directory.
"""

import ctypes
from ctypes import wintypes
import sys
import os
from pathlib import Path

def delete_nul_file(file_path=None):
    """
    Delete a NUL device file using Windows API.
    
    Args:
        file_path: Path to the nul file. If None, uses current directory.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if file_path is None:
        file_path = Path.cwd() / 'nul'
    else:
        file_path = Path(file_path)
    
    # Check if running on Windows
    if os.name != 'nt':
        print("This script is for Windows only")
        return False
    
    # Use Windows API to delete the special file
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    DeleteFileW = kernel32.DeleteFileW
    DeleteFileW.argtypes = [wintypes.LPCWSTR]
    DeleteFileW.restype = wintypes.BOOL
    
    # Convert to extended path format to bypass name checking
    extended_path = f'\\\\?\\{file_path.absolute()}'
    
    print(f"Attempting to delete: {file_path}")
    
    if DeleteFileW(extended_path):
        print("Successfully deleted nul file")
        return True
    else:
        error = ctypes.get_last_error()
        print(f"Failed to delete nul file. Error code: {error}")
        
        # Try alternative approach using cmd
        import subprocess
        cmd_path = f'"\\\\?\\{file_path.absolute()}"'
        result = subprocess.run(['cmd', '/c', 'del', cmd_path], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("Deleted using cmd")
            return True
        else:
            print(f"Could not delete the file: {result.stderr}")
            return False

def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) > 1:
        # Path provided as argument
        file_path = sys.argv[1]
    else:
        # Look for nul in current directory
        file_path = None
    
    success = delete_nul_file(file_path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()