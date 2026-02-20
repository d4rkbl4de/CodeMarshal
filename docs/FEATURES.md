# CodeMarshal Feature Matrix

**Version:** 2.2.0  
**Last Updated:** February 20, 2026

---

## Current Product State

- Completed roadmap phases: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`
- Latest local validation run (`python -m pytest -q`): `274 collected, 274 passed, 0 failed`
- Coverage policy: `fail_under = 90%`

---

## Core Capability Areas

### Investigation and Observation

- `investigate` command with scoped and intent-driven investigations
- `observe` command for direct fact collection
- Constitutional observation mode (`--constitutional`)
- Persisted observation support (`--persist`)

### Query and Analysis

- Question types: `structure`, `purpose`, `connections`, `anomalies`, `thinking`
- Limit and focus controls (`--limit`, `--focus`)
- Analyzer expansion for structure/connection/anomaly depth

### Search and Pattern Detection

- Regex search with context and filtering (`search`)
- Search limit control (`--limit`, `-m`)
- Files-only result mode (`--files-with-matches`, `-l`)
- Semantic and hybrid search support (`search --semantic`, `search --hybrid`)
- Pattern commands: `list`, `scan`, `add`, `search`, `apply`, `create`, `share`
- Built-in and custom pattern workflows

### Multi-Language Observation

- Language detector
- JavaScript/TypeScript import/export support
- Java import/class support
- Go import/export support

### Export and Visualization

Supported formats:

- `json`
- `markdown`
- `html`
- `plain`
- `csv`
- `jupyter`
- `pdf`
- `svg`

Advanced export components are implemented and tested:

- Jupyter exporter
- PDF exporter
- SVG exporter

Desktop UX enhancements:

- First-run onboarding dialog with guided setup
- Contextual hints in core workflow screens
- Inline validation for common input errors
- Summary/raw result viewer with one-click copy actions
- Accessibility mode (standard/high-contrast) with persisted font scaling
- Keyboard-first focus order and shortcut discoverability

### Storage and Data Layer

- Schema migration flow
- Transactional storage components
- Knowledge graph, history, and recommendations storage
- Collaboration storage for encrypted shares/comments/team metadata

### Knowledge and Collaboration

- Knowledge timeline/history retrieval (`history`)
- Graph projection and traversal queries (`graph`)
- Recommendation generation from investigation artifacts (`recommendations`)
- Team management, encrypted sharing, and threaded comments (`team`, `share`, `comment`)

### Integrations and Extensibility

- IDE integration foundations present (VS Code, Neovim, JetBrains)
- Plugin system foundations and loader scaffolding

### Quality and Validation

- Full pytest suite is maintained with active regression tracking
- Coverage gate enforcement (`fail_under = 90`)
- Invariant tests and integration coverage

---

## Phase-to-Feature Mapping

| Phase | Major Feature Group | Status |
| --- | --- | --- |
| 0 | Foundation repair and import-chain stability | Complete |
| 1 | Pattern system renaissance | Complete |
| 2 | Inquiry engine expansion | Complete |
| 3 | Multi-language support | Complete |
| 4 | IDE integration suite foundations | Complete |
| 5 | Desktop GUI | Complete |
| 6 | Storage and data layer | Complete |
| 7 | Test suite completion and coverage gate | Complete |
| 8 | Advanced export and visualization | Complete |
| 9 | Plugin system foundations | Complete |

---

## Remaining Work

v2.2.0 release hardening remains: packaging verification, release metadata, and final release-candidate checklist execution.

---

## Related Documentation

- **[ROADMAP.md](../ROADMAP.md)** - Execution status and follow-up milestones
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and migration guides
- **[docs/USER_GUIDE.md](USER_GUIDE.md)** - Command usage and tutorials
- **[docs/architecture.md](architecture.md)** - System architecture and design
- **[docs/index.md](index.md)** - Documentation navigation guide

---

**Feature Matrix Version: 2.2.0**  
**Last Updated: February 20, 2026**
