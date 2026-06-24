# Changelog

All notable changes to the Folder DateTime Fix project are documented here.

## [0.7.3] - 2026-06-24

### Fixed
- **Restored UNC / network-path support** that had silently broken against
  unctools 0.2.x. unctools' 0.2.0 "probe-not-mutate" surgery removed
  `normalize_path`, so the single `from unctools import (...)` block in
  `unc_handler` failed entirely on that one missing name -- disabling *all*
  unctools functionality (`UNCTOOLS_AVAILABLE` stuck `False`) even though the
  other seven functions were still present.

### Changed
- **Path normalization now delegates to `dazzle-filekit`**
  (`normalize_cross_platform_path`) -- the canonical owner of path normalization
  since the unctools probe-not-mutate split (L0 = path identity, L1 =
  normalization). `dazzle-filekit>=0.3.0` is now a required dependency; the
  hand-rolled fallback normalization was removed.
- Migrated `unctools.get_path_type` to its renamed replacement
  `classify_path_origin` (the old name is a deprecation shim removed in
  unctools 0.3.0).

## [0.7.2] - 2025-09-23

### Added
- Complete GPL-3.0 LICENSE file
- Comprehensive troubleshooting documentation (docs/Troubleshooting.md)
- Regression tests for DazzleTreeLib Issues #15, #16, #17
- Performance benchmarking framework for validation
- Multi-OS CI/CD testing (Ubuntu, Windows, macOS)
- Dynamic GitHub release version badges
- Python 3.12 support in CI/CD matrix

### Changed
- **Major Documentation Overhaul**: Transformed README from technical reference to user-focused guide
- Moved verbose debugging information to dedicated troubleshooting guide
- Fixed ASCII tree diagrams for proper depth visualization
- Adapted to DazzleTreeLib's integer-based cache depth tracking (Issue #17)
- Improved error handling for async iteration with ErrorHandlingAdapter

### Fixed
- Critical exclusion filter bug in DazzleTreeLib integration
- Permission-denied path handling with robust error recovery
- Test failures related to node tracking in cache completeness

### Removed
- Python 3.7 support (end of life)

## [0.7.1] - 2025-09-03

### Added
- **DazzleTreeLib Integration**: Complete migration to external tree traversal library
  - 82% code reduction through library use
  - PolicyDrivenErrorAdapter for robust error handling
  - Unlimited cache depth support (previously capped at 3)
- Advanced error handling for permission-denied paths
- Node-based cache completeness tracking

### Changed
- Replaced internal tree traversal with DazzleTreeLib >= 0.9.2
- Migrated from enum-based to integer-based cache depth tracking
- Improved adapter stack implementation for tree operations

### Fixed
- Cache completeness calculation for deep directory structures
- Exclusion filter propagation through adapter layers

## [0.5.5] - 2025-08-30

### Added
- **Modular Help System**: Revolutionary context-aware help architecture
  - 8 specialized topic sections
  - "Define once, use many" principle
  - Shared content across commands
- Advanced exclude/include pattern system with glob support
- Tree visualization tools for folder structure
- FolderOnlyStrategy and TreeStrategy implementations

### Fixed
- Pre-commit hook for proper version updates
- Help text formatting and user experience improvements

## [0.5.4] - 2025-08-29

### Added
- **Smart Caching System**: 57%+ performance improvement
  - Cache completeness tracking
  - Early termination optimization
  - Low-memory mode for massive file sets
- Analysis strategies (auto, tree, low-memory)
- Max depth detection for performance optimization

### Changed
- Default behavior now automatically skips system files
- Improved strategy selection heuristics

## [0.5.3] - 2025-08-29

### Added
- Multi-level verbosity system with function tracing
- Dynamic version tracking with git hooks
- Backward compatibility for legacy commands

### Fixed
- Strategy help text and formatting
- User experience improvements

## [0.5.0] - 2025-08-28

### Added
- **Core Functionality**: Initial public release
  - Fixes folder timestamps corrupted by Windows system files
  - Depth-based processing with configurable levels
  - UNC path support for network shares
  - Dry-run mode for safe previews
- Comprehensive unit test suite
- Multiple processing strategies (shallow, deep, smart)
- System file exclusion (thumbs.db, desktop.ini, .DS_Store)

### Infrastructure
- RepoKit project structure
- GitHub Actions CI/CD pipeline
- PyPI-ready packaging configuration
- VS Code development environment

## [0.1.0] - 2025-08-28

### Initial Development
- Basic folder datetime correction functionality
- Command-line interface
- Initial documentation

---

## Version History Summary

### Major Milestones
- **0.5.x**: Foundation and core features
- **0.7.x**: Architectural revolution with DazzleTreeLib
- **Current**: Production-ready with full CI/CD and documentation

### Performance Evolution
- v0.5.0: Baseline implementation
- v0.5.4: 57%+ performance improvement with caching
- v0.7.x: 82% code reduction through library integration

### Key Statistics
- 188+ comprehensive tests
- 3 operating systems tested
- 5 Python versions supported (3.8-3.12)
- 57%+ performance improvement achieved
- 82% code reduction through DazzleTreeLib

[0.7.2]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.7.2
[0.7.1]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.7.1
[0.5.5]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.5.5
[0.5.4]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.5.4
[0.5.3]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.5.3
[0.5.0]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.5.0
[0.1.0]: https://github.com/djdarcy/folder-datetime-fix/releases/tag/v0.1.0