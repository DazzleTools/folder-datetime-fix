"""
Function tracing utilities for debug output.
"""

import functools
import inspect
from pathlib import Path

# Global verbosity level (set by main program)
_verbosity_level = 0

def set_verbosity(level: int):
    """Set the global verbosity level for tracing."""
    global _verbosity_level
    _verbosity_level = level

def trace(func):
    """
    Decorator to trace function calls when verbosity >= 4.
    Shows function entry and exit with arguments and return values.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _verbosity_level
        
        if _verbosity_level >= 4:
            # Get function signature info
            module = inspect.getmodule(func)
            module_name = module.__name__ if module else "unknown"
            func_name = func.__name__
            
            # Format arguments
            args_repr = []
            
            # Handle self/cls for methods
            if args and hasattr(args[0], '__class__'):
                if func_name != '__init__':
                    args_repr.append('self')
                    remaining_args = args[1:]
                else:
                    remaining_args = args
            else:
                remaining_args = args
            
            # Add remaining positional arguments
            for arg in remaining_args:
                if isinstance(arg, Path):
                    args_repr.append(f"Path('{arg}')")
                elif isinstance(arg, str) and len(arg) > 50:
                    args_repr.append(f"'{arg[:47]}...'")
                elif isinstance(arg, list) and len(arg) > 3:
                    args_repr.append(f"[...{len(arg)} items...]")
                else:
                    args_repr.append(repr(arg))
            
            # Add keyword arguments
            for key, value in kwargs.items():
                if isinstance(value, Path):
                    args_repr.append(f"{key}=Path('{value}')")
                elif isinstance(value, str) and len(value) > 50:
                    args_repr.append(f"{key}='{value[:47]}...'")
                else:
                    args_repr.append(f"{key}={repr(value)}")
            
            args_str = ', '.join(args_repr)
            
            # Print entry
            print(f"[TRACE] >> {module_name}.{func_name}({args_str})")
            
            try:
                # Call the actual function
                result = func(*args, **kwargs)
                
                # Print exit with return value (if not None)
                if result is not None:
                    if isinstance(result, list) and len(result) > 3:
                        result_repr = f"[...{len(result)} items...]"
                    elif isinstance(result, str) and len(result) > 50:
                        result_repr = f"'{result[:47]}...'"
                    else:
                        result_repr = repr(result)
                    print(f"[TRACE] << {module_name}.{func_name} returned: {result_repr}")
                
                return result
                
            except Exception as e:
                # Print exception
                print(f"[TRACE] !! {module_name}.{func_name} raised: {type(e).__name__}: {str(e)}")
                raise
        else:
            # Normal execution without tracing
            return func(*args, **kwargs)
    
    return wrapper