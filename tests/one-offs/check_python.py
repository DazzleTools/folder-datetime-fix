#!/usr/bin/env python3
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path:")
for path in sys.path:
    print(f"  {path}")