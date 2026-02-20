# CodeMarshal Roadmap

**Roadmap Version:** 2.2.0  
**Last Updated:** February 20, 2026  
**Canonical Release Tracking:** This file is the source of truth for phase status and release gates.

## Release Snapshot

- **Current stable release line:** `v2.2.0` (GA hardening in progress)
- **Next planned release line:** `v2.3.0`
- **Quality baseline:** 90%+ coverage gate and zero release-blocking failures

## Phase Execution Status

| Phase | Name | Status | Target Window | Notes |
| --- | --- | --- | --- | --- |
| 0 | Foundation & Constitutional Baseline | Done | Completed | Stable |
| 1 | Investigation Core | Done | Completed | Stable |
| 2 | Query & Reporting Core | Done | Completed | Stable |
| 3 | Multi-Language Support | Done | Completed | Stable |
| 4 | IDE Integration Foundations | Done | Completed | Stable |
| 5 | Desktop GUI | Done | Completed | Stable |
| 6 | Storage & Data Layer | Done | Completed | Stable |
| 7 | Real-Time + Semantic + Knowledge + Collaboration | Done | Completed | Stable with environment-dependent semantic benchmarking |
| 8 | Advanced Export & Visualization | Done | Completed | PDF requires native dependencies/runtime |
| 9 | Plugin System Foundation | Done | Completed | Marketplace foundation present |
| 10 | Release Readiness (v2.2.0 GA) | In Progress | Week of Feb 20, 2026 | Must close GA gates below |
| 11 | IDE Integration Polish | Planned | March 2026 | JetBrains/VS Code/Neovim enhancements |
| 12 | Performance Optimization | Planned | March-April 2026 | Large-repo and export throughput |
| 13 | Plugin Ecosystem Evolution | Planned | April 2026 | Compatibility and distribution |
| 14 | Collaboration Enhancements | Planned | April-May 2026 | Permissions and versioned shares |
| 15 | Testing & Quality Expansion | Planned | May 2026 | Regression/performance/cross-platform gates |
| 16 | Documentation & UX Completion | Planned | May-June 2026 | Tutorials, guides, onboarding |

## Phase 10: v2.2.0 GA Gates

### Gate A: Version and Documentation Alignment

- [x] Python package metadata aligned to `2.2.0`
- [x] IDE plugin manifests aligned to `2.2.0`
- [x] Documentation version markers updated to `2.2.0`
- [x] Changelog includes dedicated GA entry

### Gate B: Artifact Validation

- [x] Python package install and smoke checks pass
- [x] Full regression suite passes
- [x] VS Code extension build (and VSIX package) passes
- [x] JetBrains `buildPlugin` passes on network-enabled CI and artifact is archived
- [x] Windows GUI packaging produces `CodeMarshal.exe`
- [ ] Docker builds validate runtime dependencies (including PDF path) - blocked: Docker CLI unavailable in this environment

### Gate C: Release Control

- [x] GA checklist captured with timestamped command evidence
- [x] Tagging policy applied for GA
- [ ] `v2.2.0` tag created on validated commit
- [x] Release notes published from changelog

## Tagging Policy (Effective Immediately)

- Use **SemVer with `v` prefix** for all new tags.
- GA tags: `vX.Y.Z`
- Pre-release tags: `vX.Y.Z-beta.N`, `vX.Y.Z-rc.N`
- Historical mixed tags are preserved for traceability but considered legacy.

## Milestones

### v2.2.0 GA Completion Milestone

- Close all Phase 10 gates.
- Publish validated artifacts for CLI, GUI, VS Code, JetBrains, Docker.

### v2.3.0 Milestone Sequence

1. IDE integration polish complete (Phase 11).
2. Performance targets met for large repositories and exports (Phase 12).
3. Plugin ecosystem and collaboration enhancements complete (Phases 13-14).
4. Quality/documentation completion and GA readiness (Phases 15-16).

## Risk Watchlist

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| JetBrains dependency resolution failures | Medium | High | Keep dedicated CI job with artifact upload and actionable logs |
| PDF export native dependency drift | Medium | Medium | Validate containerized export path in CI |
| Cross-platform packaging regressions | Medium | Medium | Maintain Linux + Windows validation matrix |

## Ownership Model

- **Release owner:** Maintainer on duty for current milestone
- **Validation owner:** CI/release engineer
- **Documentation owner:** Maintainer + reviewer pair
- **Sign-off rule:** At least one maintainer plus one reviewer for GA release gates
