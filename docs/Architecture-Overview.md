# Architecture Overview

## System Design Philosophy

The folder-datetime-fix tool is designed with a modular, extensible architecture that separates concerns into distinct layers:

1. **Command-line Interface** (CLI) - User interaction layer
2. **Analysis Strategies** - Different approaches to folder traversal
3. **Folder Scanner** - Core timestamp computation engine  
4. **Cache System** - Performance optimization with completeness tracking
5. **Visualization** - Tree rendering and progress display
6. **Timestamp Fixer** - Actual filesystem modification

## Component Interaction Diagram

```
User Input (CLI)
    ↓
┌─────────────────────────────────────────────────┐
│               cli.py (main)                     │
│  - Parses arguments (--depth, --strategy, etc)  │
│  - Selects analysis strategy via --analyze      │
│  - Configures scanner and fixer                 │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│          StrategyFactory.create_strategy()      │
│  - Creates appropriate strategy instance        │
│  - Applies modifiers (no-cache, etc)            │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│           AnalysisStrategy (Abstract)           │
│  - StandardStrategy (uses scan_and_collect)     │
│  - LowMemoryStrategy (no cache)                 │
│  - TreeStrategy (bottom-up with tree)           │
│  - FolderOnlyStrategy (minimal memory)          │
│  - AutoStrategy (adaptive selection)            │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│              FolderScanner                      │
│  - get_shallow_timestamp()                      │
│  - get_deep_timestamp()                         │
│  - get_smart_timestamp()                        │
│  - scan_and_collect() [main workhorse]          │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│           SmartStreamingCache                   │
│  - get_or_compute() with CacheCompleteness      │
│  - Tracks: NONE, SHALLOW, PARTIAL_2/3, COMPLETE │
│  - Memory-bounded with LRU eviction             │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│            FolderTimestampFixer                 │
│  - fix_folder_timestamp()                       │
│  - Applies computed timestamps to folders       │
└─────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Strategy Pattern for Analysis

Different analysis strategies implement the same `AnalysisStrategy` interface:

```python
class AnalysisStrategy(ABC):
    @abstractmethod
    def analyze(self, base_path: Path, depths: List[int]) -> List[Tuple[Path, Optional[datetime]]]:
        pass
```

This allows runtime selection via `--analyze`:
- `--analyze=tree` → TreeStrategy
- `--analyze=folder-only` → FolderOnlyStrategy
- `--analyze=low-memory` → LowMemoryStrategy
- `--analyze=auto` → AutoStrategy (selects based on path characteristics)

### 2. Cache Completeness Tracking

The cache system tracks how thoroughly each folder has been scanned:

```python
class CacheCompleteness(Enum):
    NONE = 0           # Not scanned
    SHALLOW = 1        # Immediate children only
    PARTIAL_2 = 2      # 2 levels deep
    PARTIAL_3 = 3      # 3 levels deep
    COMPLETE = 999     # Fully recursive
```

This enables intelligent cache reuse:
- If a folder is marked `COMPLETE`, no need to rescan
- If marked `PARTIAL_2` but we need depth 3, rescan required
- If marked `COMPLETE` but we only need depth 1, use cached data

### 3. Separation of Concerns

Each component has a single responsibility:

| Component | Responsibility |
|-----------|---------------|
| **CLI** | Parse arguments, coordinate components |
| **AnalysisStrategy** | Decide HOW to traverse folders |
| **FolderScanner** | Compute timestamps for folders |
| **SmartStreamingCache** | Store and retrieve computed results |
| **FolderTimestampFixer** | Apply timestamps to filesystem |
| **TreeVisualizer** | Render folder structures |

## How Components Interact

### StandardStrategy Flow

1. CLI creates `StandardStrategy` with a `FolderScanner`
2. StandardStrategy calls `scanner.scan_and_collect()`
3. Scanner uses cache via `cache.get_or_compute()`
4. Cache checks completeness and returns cached or computes new
5. Results returned to strategy → CLI → Fixer

### TreeStrategy Flow

1. CLI creates `TreeStrategy` with a `FolderScanner`
2. TreeStrategy builds its own tree structure
3. During tree building, checks cache for complete branches
4. Computes timestamps bottom-up (children before parents)
5. Stores results back to cache with completeness levels
6. Returns results for requested depths

### FolderOnlyStrategy Flow

1. CLI creates `FolderOnlyStrategy` with a `FolderScanner`
2. Strategy does its own `os.walk()` traversal
3. For each folder:
   - Checks cache for sufficient completeness
   - If cache hit, uses cached timestamp
   - If cache miss, computes timestamp on-the-fly
   - Stores result in cache with completeness level
4. Prunes traversal when complete folders found

## Cache Integration Points

### Where Cache is Used

1. **FolderScanner methods**:
   - `get_shallow_timestamp()` → `cache.get_or_compute(path, "shallow")`
   - `get_deep_timestamp()` → `cache.get_or_compute(path, "deep")`
   - `get_smart_timestamp()` → `cache.get_or_compute(path, "smart")`

2. **FolderOnlyStrategy**:
   - Checks cache before computing
   - Stores results with completeness
   - Prunes traversal on complete folders

3. **TreeStrategy** (after fixes):
   - Checks cache during tree building
   - Stores computed timestamps with completeness
   - Prunes complete branches

### Cache Completeness Logic

```python
# When storing in cache:
if not has_subdirs:
    completeness = COMPLETE
elif at_max_depth:
    completeness = SHALLOW
else:
    remaining_depth = max_depth - current_depth
    completeness = from_depth(remaining_depth)

# When checking cache sufficiency:
if cached.completeness == COMPLETE:
    return True  # Always sufficient
if needed_depth <= cached_actual_depth:
    return True  # Have enough depth
return False  # Need to recompute
```

## Extensibility Points

### Adding New Analysis Strategies

1. Create class extending `AnalysisStrategy`
2. Implement `analyze()` method
3. Add to `StrategyFactory.create_strategy()`
4. Update `get_available_strategies()`

Example:
```python
class CustomStrategy(AnalysisStrategy):
    def analyze(self, base_path: Path, depths: List[int]):
        # Custom traversal logic
        # Can use self.scanner for timestamp computation
        # Should integrate with cache for performance
        pass
```

### Adding New Visualization Modes

1. Extend `TreeVisualizer` or create new visualizer
2. Add to CLI options
3. Integrate with processing loop

### Custom Cache Implementations

The cache interface is simple:
```python
cache.get_or_compute(path, strategy) -> (mtime, completeness)
cache.cache[path] = SmartCacheEntry(...)
```

Could replace with Redis, SQLite, or other backends.

## Performance Considerations

### Memory Usage

| Strategy | Memory per 10K folders | Use Case |
|----------|------------------------|----------|
| folder-only | ~1MB | Ultra-minimal |
| low-memory | <1MB | Massive trees |
| tree | ~2MB | Deep hierarchies |
| standard | ~3.5MB | General use |

### Cache Hit Rates

With completeness tracking:
- First run: 0% hit rate (cold cache)
- Second run (same depths): 95-100% hit rate
- Incremental deeper: 50-80% hit rate (reuses shallow)

### Traversal Optimization

- **Pruning**: Stop traversing when complete folders found
- **Depth filtering**: Only process requested depths
- **System file skipping**: Ignore `__pycache__`, `.git`, etc.

## Configuration Flow

```
CLI Arguments
    ↓
--analyze=tree,no-cache  (comma-separated modifiers)
    ↓
StrategyFactory.create_strategy()
    ↓
Parse: strategy="tree", modifiers=["no-cache"]
    ↓
Create TreeStrategy
    ↓
Apply modifiers (disable cache)
    ↓
Return configured strategy
```

## Testing Architecture

### Unit Tests
- `test_analysis_strategies.py` - Strategy implementations
- `test_cache_completeness.py` - Cache completeness logic
- `test_folder_scanner.py` - Scanner methods
- `test_tree_strategy.py` - Tree-specific tests
- `test_folderonly_completeness.py` - FolderOnly cache integration

### Integration Tests
- Full pipeline tests with real directory structures
- Cache persistence across runs
- Performance benchmarks

## Future Enhancements

### Planned Features

1. **`--depth-to N`** - Specify range 0 to N easily
2. **Parallel processing** - Multi-threaded traversal
3. **Remote caching** - Shared cache across machines
4. **Watch mode** - Monitor and fix in real-time

### Extension Points

1. **Plugin system** for custom strategies
2. **Export formats** for analysis results
3. **Web UI** for visualization
4. **API mode** for integration

## Summary

The architecture is designed for:
- **Modularity**: Each component has a single responsibility
- **Extensibility**: Easy to add new strategies and features
- **Performance**: Cache with completeness tracking
- **Flexibility**: Multiple strategies for different use cases
- **Testability**: Clear interfaces and separation of concerns

The key insight is that **analysis strategies** control HOW to traverse, while **FolderScanner** computes timestamps, and **SmartStreamingCache** optimizes performance with completeness tracking. This separation allows for powerful combinations like `--analyze=tree,no-cache` or `--analyze=auto --strategy=deep`.