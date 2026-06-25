"""
Backward compatibility module - redirects to cache_wrapper.

This module maintains backward compatibility by re-exporting all
symbols from cache_wrapper. The actual implementation now uses
DazzleTreeLib's improved integer-based depth tracking system.

Issue #17 Resolution: Replaced enum-based CacheCompleteness with
integer-based depth tracking that supports unlimited depth levels.
"""

# Import everything from the new wrapper
from .cache_wrapper import (
    CacheCompleteness,
    SmartCacheEntry,
    SmartStreamingCache,
    SyncCacheWrapper,
    CacheEntry,
    DAZZLETREELIB_AVAILABLE,
)

__all__ = [
    'CacheCompleteness',
    'SmartCacheEntry',
    'SmartStreamingCache',
    'SyncCacheWrapper',
    'CacheEntry',
    'DAZZLETREELIB_AVAILABLE',
]