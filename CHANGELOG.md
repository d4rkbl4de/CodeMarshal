# CodeMarshal Changelog

All notable changes to CodeMarshal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

See [ROADMAP.md](ROADMAP.md) for detailed execution status and remaining work.

## Migration Guide

### From v1.x to v2.0+
CodeMarshal v2.0+ is a complete architectural redesign. Investigations from v1.x are not compatible. To migrate:

1. Install v2.0+: `pip install -e .`
2. Re-run investigations on your codebase
3. Use new export formats for preserved results

### From v2.0.0 to v2.1.0
No breaking changes. New features are additive only.

---

**Full documentation available at:**
- [README.md](README.md) - Project overview and quick start
- [ROADMAP.md](ROADMAP.md) - Execution status and milestones
- [docs/](docs/) - Complete documentation suite
