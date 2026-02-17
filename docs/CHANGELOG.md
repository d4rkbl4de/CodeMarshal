# CodeMarshal Changelog

All notable changes to CodeMarshal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0-rc1] - 2026-02-16

### Summary

Release candidate for v2.2.0 with roadmap phases 1-7 implemented and release-hardening updates applied.

**Test Status:** 274 passed, 0 failed  
**Validation Command:** `python -m pytest -q`

### Added

- Real-time investigation foundations:
  - file watcher and diff sight modules
  - CLI watch/diff/status command surface
- Semantic search stack:
  - semantic sight and embedding storage
  - semantic search command paths in CLI/TUI integrations
- Knowledge base stack:
  - history, graph, and recommendations modules
  - knowledge storage and CLI command handlers
- Pattern marketplace + template workflows:
  - marketplace, collector, and template modules
  - CLI pattern search/apply/create/share command flows
- Collaboration stack:
  - encrypted sharing, team, and threaded comments modules
  - collaboration storage and collaboration CLI command flows
- Desktop GUI phase-7 widgets:
  - diff viewer, templates panel, marketplace panel
  - knowledge canvas, history sidebar, comments panel

### Fixed

- Optional dependency resilience for semantic import paths when numpy/semantic stack is unavailable.
- Windows test reliability issues caused by host temp-directory ACL behavior.
- Windows atomic rename transient lock behavior via retry-safe atomic replace.

### Changed

- Core package metadata advanced to `2.2.0rc1`.
- Documentation status synchronized for release-candidate validation baseline.
- Release-candidate artifact hygiene improved with additional runtime/test-path ignore rules.

### Known Limitations

1. **PDF Export:** still depends on WeasyPrint native rendering libraries or containerized Linux runtime.
2. **Semantic quality/performance metrics:** benchmark targets remain environment-dependent and should be validated on representative repositories before final GA.

## [2.1.1] - 2026-02-14

### Summary

Maintenance release focused on reliability hardening after the Phase 5 desktop GUI delivery.

**Test Status (with PySide6):** 186 passed, 2 skipped  
**Coverage (with PySide6):** 95.70% (gate: 90%)

### Added

- Import-signature anchor generator for `ContentFingerprintMethod.IMPORT_SIGNATURE`
- Recovery compatibility helper module (`integrity/recovery/_compat.py`)
- Headless GUI smoke CI job for PySide6 desktop tests
- New maintenance tests:
  - `tests/test_recovery_maintenance.py`
  - `tests/test_anchor_import_signature.py`
  - `tests/test_shutdown_manager.py`

### Fixed

- Backup/restore schema compatibility between `snapshot` and legacy `observations` payload keys
- Incremental backup implementation with parent-chain materialization during restore
- Hardcoded recovery version metadata (`\"1.0.0\"`) replaced with runtime package version resolution
- Shutdown manager integration with atomic write flush, corruption checks, and session-state persistence
- Deterministic integrity hash validation for legacy and current backup formats

### Changed

- Backup format metadata advanced to v2 canonical hashing while preserving compatibility validation
- Invariant guardrails strengthened for duplicate pattern IDs and constitutional documentation checks
- Documentation status synchronized across README, roadmap, and docs index/user guide

## [2.1.0] - 2026-02-13

### Summary

This release completes phases 0 through 9 of the roadmap, including the desktop GUI implementation in Phase 5.

**Test Status:** 175 passed, 3 skipped  
**Coverage:** 93.53% (gate: 90%)

### Added

#### Phase 3: Multi-Language Support (Complete)

- Language detector for automatic language identification
- JavaScript/TypeScript import/export support (`javascript_sight.py`)
- Java import/class support (`java_sight.py`)
- Go import/export support (`go_sight.py`)

#### Phase 4: IDE Integration Suite (Complete)

- VS Code extension foundation
- Neovim plugin foundation
- JetBrains plugin foundation
- Editor integration API (`bridge/integration/editor.py`)

#### Phase 6: Storage & Data Layer (Complete)

- Schema migration system (`storage/migration.py`)
- Transactional storage components
- Knowledge base scaffolding
- Atomic write guarantees
- Corruption detection

#### Phase 8: Advanced Export & Visualization (Complete)

- Jupyter notebook exporter (`bridge/integration/jupyter_exporter.py`)
- PDF exporter with WeasyPrint (`bridge/integration/pdf_exporter.py`)
- SVG exporter for architecture diagrams (`bridge/integration/svg_exporter.py`)
- HTML exporter with interactive features
- CSV exporter for data analysis

#### Phase 9: Plugin System (Complete)

- Plugin API foundation
- Plugin loader scaffolding
- Pattern engine with context-aware detection
- Statistical outlier identification (z-score)
- Built-in pattern libraries:
  - Security patterns (8 patterns)
  - Performance patterns (20 patterns)
  - Style patterns (15 patterns)
  - Architecture patterns (12 patterns)

#### New Commands

- `search` - Regex/text search with context and filtering
- `pattern` - Pattern detection and management (list, scan, add)
- `config` - Configuration management (show, edit, reset, validate)
- `backup` - Backup operations
- `cleanup` - Cleanup operations
- `repair` - Repair operations
- `migrate` - Schema migration
- `gui` - Desktop GUI entrypoint (PySide6-based)

### Enhanced

#### Investigation & Observation

- Extended analyzer behavior for structure/connections/anomalies
- Constitutional observation mode (`--constitutional`)
- Persisted observation support (`--persist`)
- Import-chain fixes for test stability

#### Query System

- Question types: `structure`, `purpose`, `connections`, `anomalies`, `thinking`
- Limit and focus controls (`--limit`, `--focus`)
- Enhanced query engine performance

#### Search Capabilities

- Result limit control (`--limit`, `-m`)
- Files-only result mode (`--files-with-matches`, `-l`)
- Context lines support (`-C`)
- Glob pattern filtering (`-g`)
- Type filtering (`-t`)
- Case-insensitive search (`-i`)
- Multi-threaded search with `--threads`

#### Export System

- All export formats now have comprehensive test coverage
- PDF export with Docker support documentation
- SVG generation for architecture visualization

### Fixed

#### Foundation (Phase 0)

- Import-chain fixes landed
- Test discovery stabilized
- Full test suite operational (175 passed, 3 skipped)

#### Coverage

- Coverage gate enforcement now at 93.53% (exceeds 90% minimum)
- Invariant tests for observation layer
- Integration test coverage expanded

### Documentation

- Added comprehensive API documentation
- Created integration examples for CI/CD, editors, and scripting
- Documented Docker setup for PDF export
- Added architecture documentation with layer-by-layer breakdown
- Created directory structure documentation
- Improved cross-references between documents

### Completed

#### Phase 5: Desktop GUI

- Implemented five functional screens: Home, Observe, Investigate, Patterns, Export
- Added async bridge/runtime integration with worker-thread execution
- Added progress, cancellation, and GUI error handling flow
- Added desktop session state persistence and recovery scaffolding

**Note:** GUI requires `pip install -e .[gui]` for PySide6 dependency. GUI tests skip when optional dependency is unavailable.

### Known Limitations

1. **PDF Export:** Requires native libraries (GTK on Windows, Cairo/Pango on Linux) or Docker container.
2. **Optional GUI Dependency:** GUI runtime/tests require PySide6 and are skipped when unavailable.

### Dependencies

#### Core

- Python 3.11+
- No external dependencies for core functionality

#### Optional Extras

- `[gui]` - PySide6 for desktop GUI
- `[export_pdf]` - WeasyPrint and native rendering libraries
- `[dev]` - Development dependencies (pytest, coverage, etc.)

## [2.0.0] - 2026-02-07

### Initial v2.0 Release

Complete rewrite with truth-preserving architecture:

### Added

- Five-layer architecture (Observations, Inquiry, Interface, Bridge, Core)
- Constitutional framework with 24 articles
- Immutable observation system with cryptographic integrity
- Question-driven investigation workflow
- Pattern detection with uncertainty quantification
- TUI (Terminal User Interface)
- CLI with comprehensive command set
- Export formats: JSON, Markdown, HTML, Plain Text, CSV

### Core Philosophy

- **Law 1:** Witness, Don't Interpret
- **Law 2:** Support, Don't Replace
- **Law 3:** Clarify, Don't Obscure

---

## Roadmap Reference

See [ROADMAP.md](../ROADMAP.md) for detailed execution status and remaining work.

## Migration Guide

### From v1.x to v2.0+

CodeMarshal v2.0+ is a complete architectural redesign. Investigations from v1.x are not compatible. To migrate:

1. Install v2.0+: `pip install -e .`
2. Re-run investigations on your codebase
3. Use new export formats for preserved results

### From v2.0.0 to v2.1.0

No breaking changes. New features are additive only.

### From v2.1.0 to v2.1.1

No breaking CLI/API changes. This release is reliability and maintenance focused.

---

**Full documentation available at:**

- [README.md](../README.md) - Project overview and quick start
- [ROADMAP.md](../ROADMAP.md) - Execution status and milestones
- [docs/index.md](index.md) - Complete documentation suite
