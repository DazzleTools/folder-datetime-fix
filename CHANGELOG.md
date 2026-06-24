# Changelog

All notable changes to the Folder DateTime Fix project are documented here.

## [0.7.5] - 2026-06-24

### Fixed
- **Two CI test failures unmasked by 0.7.4.** Declaring the runtime deps in
  0.7.4 let the previously-uncollectable tests run, surfacing two pre-existing
  issues that only appear in a clean CI environment (both verified locally on
  Windows AND WSL/Linux before pushing):
  - `pytest-asyncio` was used by the async tests (the `@pytest.mark.asyncio`
    marker and the `dazzletreelib.aio` integration tests) but never declared --
    it was only present ambiently in dev environments. CI installs only what
    `[dev]` declares, so it failed with "async def functions are not natively
    supported". Added `pytest-asyncio` to the `[dev]` extra.
  - `tests/test_unc_handler.py::test_path_normalization` asserted that a
    backslash UNC path (`\\server\share`) keeps its prefix after normalization.
    That holds only on Windows; on POSIX the path is not absolute, so the
    cross-platform normalizer absolutizes it against cwd. The assertion is now
    platform-aware (strong form on Windows, share-identity invariant on POSIX).
    A test-correctness fix -- Windows behavior is unchanged.

### Added
- `tests/one-offs/preflight_clean_venv.py` -- a clean-venv pre-flight that
  reproduces CI's environment locally (throwaway venv, `pip install -e ".[dev]"`,
  pytest), so dependency-resolution drift and ambient-package pollution are
  caught before pushing instead of by the CI run. Runs under both Windows and
  WSL/Linux Python.

## [0.7.4] - 2026-06-24

### Fixed
- **Runtime dependencies were never installed.** `pyproject.toml`'s `[project]`
  table is authoritative under PEP 621 but declared no `dependencies` (only a
  dynamic `version`), so setuptools ignored `setup.py`'s `install_requires`
  entirely. CI installed the package with none of `dazzletreelib` /
  `dazzle-filekit`, and every test importing them failed at collection
  (`ModuleNotFoundError: No module named 'dazzletreelib'`) -- red since the
  `pyproject.toml` landed. Dependencies are now declared in
  `pyproject.toml [project].dependencies`, the single authoritative location.

### Changed
- **Minimum Python is now 3.9** (was 3.8). The `dazzle-filekit` dependency pulls
  `dazzle-lib`, which requires Python >=3.9, so 3.7/3.8 are no longer
  installable. Dropped 3.7/3.8 from the CI matrices, the classifiers, and
  `requires-python`.
- Updated repository URLs to `DazzleTools/folder-datetime-fix` (moved from
  `djdarcy/modified_datetime_fix`).
- Removed the now-dead `install_requires` from `setup.py`; dependencies live
  only in `pyproject.toml`.

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
- 4 Python versions supported (3.9-3.12)
- 57%+ performance improvement achieved
- 82% code reduction through DazzleTreeLib

[0.7.2]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.7.2
[0.7.1]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.7.1
[0.5.5]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.5.5
[0.5.4]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.5.4
[0.5.3]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.5.3
[0.5.0]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.5.0
[0.1.0]: https://github.com/DazzleTools/folder-datetime-fix/releases/tag/v0.1.0