#!/usr/bin/env python3
"""
Quick test to verify permission error handling works.
"""

import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path

def test_permission_handling():
    """Test that permission errors are handled gracefully."""
    
    # Create a test directory
    test_dir = Path(tempfile.mkdtemp(prefix="permission_test_"))
    
    try:
        # Create some subdirectories
        (test_dir / "accessible").mkdir()
        (test_dir / "accessible" / "file.txt").write_text("test")
        
        # Test with --strict flag (should fail on any permission error)
        print("Testing with --strict flag on accessible directory...")
        result = subprocess.run([
            sys.executable, "-m", "folder_datetime_fix.cli",
            str(test_dir),
            "--fix-all",
            "--dry-run",
            "--strict",
            "-vv"
        ], capture_output=True, text=True)
        
        print(f"Return code: {result.returncode}")
        if result.returncode != 0:
            print("STDERR:", result.stderr)
        
        # Test without --strict flag (should continue on errors)
        print("\nTesting without --strict flag (permissive mode)...")
        result = subprocess.run([
            sys.executable, "-m", "folder_datetime_fix.cli",
            str(test_dir),
            "--fix-all", 
            "--dry-run",
            "-vv"
        ], capture_output=True, text=True)
        
        print(f"Return code: {result.returncode}")
        if result.returncode != 0:
            print("STDERR:", result.stderr)
        
        # Test on a path with known permission issues (if on Windows)
        if sys.platform == "win32":
            print("\nTesting on C:\\ with System Volume Information...")
            # Without --strict (should continue)
            result = subprocess.run([
                sys.executable, "-m", "folder_datetime_fix.cli",
                "C:\\",
                "--depth", "1",
                "--dry-run",
                "-v"
            ], capture_output=True, text=True, timeout=5)
            
            print(f"Permissive mode return code: {result.returncode}")
            if "WARNING" in result.stderr or "Permission" in result.stderr:
                print("Permission warnings detected (good!)")
                
            # With --strict (should fail if permission denied)
            result = subprocess.run([
                sys.executable, "-m", "folder_datetime_fix.cli",
                "C:\\",
                "--depth", "1",
                "--dry-run",
                "--strict",
                "-v"
            ], capture_output=True, text=True, timeout=5)
            
            print(f"Strict mode return code: {result.returncode}")
        
        print("\nPermission handling test completed successfully!")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_permission_handling()