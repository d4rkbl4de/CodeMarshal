# CodeMarshal Documentation

**Version:** 2.2.0  
**Last Updated:** February 20, 2026

Welcome to the CodeMarshal documentation. This guide helps you navigate all available documentation.

---

## Quick Start

New to CodeMarshal? Start here:

1. **[README.md](../README.md)** - Project overview, installation, and quick start
2. **[docs/USER_GUIDE.md](USER_GUIDE.md)** - Complete command reference and workflows
3. **[ROADMAP.md](../ROADMAP.md)** - Current execution status and milestones

---

## Documentation Structure

### Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Project overview, quick start, basic usage | Everyone |
| [ROADMAP.md](../ROADMAP.md) | Execution status, milestones, phase tracking | Contributors, Project Managers |
| [CHANGELOG.md](../CHANGELOG.md) | Version history, what's new, migration guides | Users, Developers |
| [docs/RELEASE_CHECKLIST_v2.2.0.md](RELEASE_CHECKLIST_v2.2.0.md) | GA gate results and release hardening checklist | Maintainers, Release Engineers |
| [docs/USER_GUIDE.md](USER_GUIDE.md) | Complete command reference and tutorials | Users |
| [docs/FEATURES.md](FEATURES.md) | Feature matrix and capability overview | Users, Evaluators |
| [docs/collaboration.md](collaboration.md) | Team, share, and encrypted comment workflows | Users, Developers |

### Architecture & Design

| Document | Purpose | Audience |
|----------|---------|----------|
| [docs/architecture.md](architecture.md) | Layer-by-layer architecture, design philosophy | Developers, Architects |
| [docs/Structure.md](Structure.md) | Directory structure and organization | Developers, Contributors |
| [docs/README.truth.md](README.truth.md) | Truth-preservation philosophy and principles | Everyone |

### API & Integration

| Document | Purpose | Audience |
|----------|---------|----------|
| [docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Programmatic API reference | Developers, Integrators |
| [docs/INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md) | CI/CD, editor, and scripting examples | DevOps, Tool Builders |

---

## By Use Case

### I want to...

**...get started quickly**
→ [README.md](../README.md) → [docs/USER_GUIDE.md](USER_GUIDE.md)

**...understand the architecture**
→ [docs/architecture.md](architecture.md) → [docs/Structure.md](Structure.md)

**...see what features are available**
→ [docs/FEATURES.md](FEATURES.md) → [CHANGELOG.md](../CHANGELOG.md)

**...integrate with my tools**
→ [docs/INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md) → [docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md)

**...contribute to the project**
→ [ROADMAP.md](../ROADMAP.md) → [docs/architecture.md](architecture.md) → [docs/Structure.md](Structure.md)

**...understand the philosophy**
→ [docs/README.truth.md](README.truth.md) → [docs/architecture.md](architecture.md)

---

## Key Concepts

### Truth-Preserving Investigation

CodeMarshal follows three core laws:

1. **Witness, Don't Interpret** - Record only what exists in source code
2. **Support, Don't Replace** - Help humans think, don't think for them
3. **Clarify, Don't Obscure** - Make reality clearer, never more confusing

Learn more: [docs/README.truth.md](README.truth.md)

### Five-Layer Architecture

1. **Observations** (Layer 1) - Immutable facts from source code
2. **Inquiry** (Layer 2) - Human questions and pattern analysis
3. **Interface** (Layer 3) - Presentation of information
4. **Bridge** (Layer 4) - Command execution and integrations
5. **Core** (Layer 5) - Runtime authority and lifecycle

Learn more: [docs/architecture.md](architecture.md)

---

## Command Quick Reference

| Command | Purpose | Documentation |
|---------|---------|---------------|
| `investigate` | Create a tracked investigation | [USER_GUIDE.md#investigate](USER_GUIDE.md#investigate) |
| `observe` | Collect observations | [USER_GUIDE.md#observe](USER_GUIDE.md#observe) |
| `query` | Ask questions about investigations | [USER_GUIDE.md#query](USER_GUIDE.md#query) |
| `search` | Search code with regex | [USER_GUIDE.md#search](USER_GUIDE.md#search) |
| `pattern` | Pattern detection and management | [USER_GUIDE.md#pattern](USER_GUIDE.md#pattern) |
| `team` | Workspace unlock and team management | [USER_GUIDE.md#collaboration-commands-team-share-comment](USER_GUIDE.md#collaboration-commands-team-share-comment) |
| `share` | Encrypted artifact sharing | [USER_GUIDE.md#collaboration-commands-team-share-comment](USER_GUIDE.md#collaboration-commands-team-share-comment) |
| `comment` | Encrypted threaded comments | [USER_GUIDE.md#collaboration-commands-team-share-comment](USER_GUIDE.md#collaboration-commands-team-share-comment) |
| `export` | Export results to various formats | [USER_GUIDE.md#export](USER_GUIDE.md#export) |
| `gui` | Launch desktop GUI | [USER_GUIDE.md#gui](USER_GUIDE.md#gui) |
| `tui` | Launch terminal UI | [USER_GUIDE.md#tui](USER_GUIDE.md#tui) |

Desktop GUI includes first-run onboarding, accessibility preferences, and in-app shortcut help (`F1`).

---

## Current Status

**Version:** 2.2.0  
**Completed Phases:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9  
**Latest Local Validation:** 274 collected, 274 passed, 0 failed  
**Coverage Policy:** `fail_under = 90`

See [ROADMAP.md](../ROADMAP.md) for detailed execution status and follow-up milestones.

---

## Support & Community

- **Issues:** Report bugs at GitHub Issues
- **Discussions:** Feature requests and questions at GitHub Discussions
- **Documentation:** This documentation suite

---

## License

See [LICENSE](../LICENSE) file for details.

---

**Documentation Index Version:** 2.2.0  
**Last Updated:** February 20, 2026
