# CodeMarshal Roadmap (Execution Status)

**Version:** 2.1.0  
**Last Updated:** February 13, 2026  
**Current Focus:** Phase 5 - Desktop GUI (CRITICAL ISSUES IDENTIFIED)

---

## Summary

Core platform work is complete across foundation, pattern system, inquiry, multi-language support, IDE integration foundations, storage/data layer, test completion, advanced export/visualization, and plugin architecture.

**Only one roadmap phase remains: Desktop GUI (Phase 5).**

**⚠️ CRITICAL:** Codebase audit reveals Phase 5 is currently **a shell without functionality**. All GUI views are placeholder implementations. See "Critical Issues" section below.

---

## Phase Status

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| 0 | Foundation Repair | Complete | Import-chain fixes landed; test discovery stabilized |
| 1 | Pattern System Renaissance | Complete | Built-in pattern libraries + engine/dashboard support present |
| 2 | Inquiry Engine Expansion | Complete | Extended analyzer behavior for structure/connections/anomalies |
| 3 | Multi-Language Support | Complete | JS/TS, Java, Go sights + language detector |
| 4 | IDE Integration Suite | Complete | VS Code / Neovim / JetBrains foundations in repo |
| 5 | Desktop GUI | **CRITICAL** | GUI shell exists but all views are placeholder implementations |
| 6 | Storage & Data Layer | Complete | Migration, transactional storage, knowledge base scaffolding |
| 7 | Test Suite Completion | Complete | Full suite passing; coverage gate exceeded |
| 8 | Advanced Export & Visualization | Complete | Jupyter, PDF, SVG exporters + tests |
| 9 | Plugin System | Complete | Plugin API and loader foundations |

---

## Latest Validation Snapshot

- Full test suite: `168 passed, 2 skipped`
- Coverage run: `96.56%` total (gate: `90%`)
- Skip reason: optional GUI dependency (`PySide6`) missing in current environment
- **pyproject.toml version:** 2.0.0 (⚠️ should be 2.1.0)

---

## Critical Issues Identified (February 13, 2026)

### 🔴 CRITICAL: GUI is Non-Functional Shell

**Current State:** All GUI views are placeholder implementations with zero functionality.

| View | Current State | Required State |
|------|---------------|----------------|
| `HomeView` | Navigation buttons only | Project browser, recent sessions, quick actions |
| `ObserveView` | Single label | File browser, observation controls, results viewer |
| `InvestigateView` | Single label | Investigation config, query builder, results display |
| `PatternsView` | Single label | Pattern library, scan controls, match visualization |
| `ExportView` | Single label | Format selection, preview, export execution |

**Root Cause:** No integration between GUI views and:

- Bridge commands (`investigate`, `observe`, `query`, `pattern`, `export`)
- Core runtime/engine
- Storage system
- Observation interfaces

### 🟠 HIGH: Version Mismatch

**Issue:** `pyproject.toml` still shows version `2.0.0` instead of `2.1.0`

- Creates confusion for users
- May cause packaging/distribution issues
- Inconsistent with documentation

### 🟡 MEDIUM: Incomplete Core Implementations

**TODOs Found in Critical Path:**

1. **observations/record/anchors.py:846**
   - Content fingerprinting using IMPORT_SIGNATURE not implemented
   - Affects observation integrity tracking

2. **integrity/recovery/restore.py:174**
   - Hardcoded `"system_version": "1.0.0"`
   - Should pull from package metadata

3. **integrity/recovery/backup.py:237, 329**
   - Incremental backup logic not implemented
   - System version hardcoded

4. **core/shutdown.py:276, 297**
   - Missing integration with storage.atomic
   - Missing integration with integrity.recovery

### 🟡 MEDIUM: Placeholder Test Suite

**tests/invariants_test.py:** Contains 14+ TODOs with no actual implementations:

- Constitutional compliance checks (Articles 1-24)
- Truth preservation validation
- Interface invariants
- Metaphor consistency
- Export integrity

These tests pass but verify nothing meaningful.

---

## Revised Phase 5: Desktop GUI Implementation

### Objective

Transform the current GUI shell into a production-ready desktop interface that provides full CLI parity through PySide6.

### Revised Timeline & Milestones

**Original Estimate:** 4 weeks (Feb 13 - Mar 8)  
**Revised Estimate:** 6 weeks (Feb 13 - Mar 22)  
**Reason:** GUI currently has zero functionality; requires complete implementation, not just "productization"

| Milestone | Target Date | Deliverable | Priority | Status |
|-----------|-------------|-------------|----------|--------|
| **Phase 5A: Foundation** | | | | |
| Fix Version Number | Feb 13, 2026 | Update pyproject.toml to 2.1.0 | 🔴 Critical | Not Started |
| GUI-Engine Bridge | Feb 14, 2026 | Integration layer between Qt signals and bridge commands | 🔴 Critical | Not Started |
| Session State Management | Feb 15, 2026 | Recent investigations, session restore, auto-save | 🟠 High | Not Started |
| **Phase 5B: Core Screens** | | | | |
| Home Screen v2 | Feb 17, 2026 | Project browser, recent list, new investigation flow | 🟠 High | Not Started |
| Observe Screen | Feb 20, 2026 | File browser, eye selection, real-time progress, results | 🔴 Critical | Not Started |
| Investigate Screen | Feb 24, 2026 | Investigation config, query interface, pattern results | 🔴 Critical | Not Started |
| Patterns Screen | Feb 27, 2026 | Pattern library, scan execution, match visualization | 🟠 High | Not Started |
| Export Screen | Mar 2, 2026 | Format selection, preview, progress, file dialogs | 🟠 High | Not Started |
| **Phase 5C: Polish** | | | | |
| Error Handling | Mar 4, 2026 | Try-catch all bridge calls, user-friendly dialogs | 🔴 Critical | Not Started |
| Progress Indicators | Mar 5, 2026 | Progress bars for long operations, cancellation support | 🟠 High | Not Started |
| Keyboard Navigation | Mar 6, 2026 | Tab order, shortcuts, accessibility | 🟡 Medium | Not Started |
| **Phase 5D: Validation** | | | | |
| Integration Testing | Mar 8, 2026 | End-to-end workflows, error scenarios | 🟠 High | Not Started |
| Cross-Platform Testing | Mar 10, 2026 | Windows, Linux, macOS validation | 🟠 High | Not Started |
| Documentation | Mar 12, 2026 | GUI user guide, troubleshooting, packaging | 🟡 Medium | Not Started |
| **Phase 5E: Release** | | | | |
| v2.1.0 Release | Mar 15, 2026 | All acceptance criteria met | 🟠 High | Not Started |

### Resource Requirements (Revised)

| Resource | Requirement | Notes |
|----------|-------------|-------|
| Development | 2 developers minimum | PySide6/Qt experience **required** |
| Architecture | Senior review | Bridge-Engine-GUI integration design |
| Testing | QA validation | Cross-platform testing (Win/Linux/macOS) |
| Documentation | Technical writer | GUI-specific user guides |
| Infrastructure | CI updates | GUI testing in headless environments |

### Required Deliverables (Revised)

#### 1. **GUI-Engine Integration Layer** (CRITICAL)

Create a bridge between Qt signals/slots and the existing bridge commands:

```python
# Example: GUICommandBridge
gui_bridge = GUICommandBridge()
gui_bridge.observe_requested.connect(run_observe_command)
gui_bridge.investigation_complete.connect(update_results_view)
```

**Requirements:**

- Async execution of bridge commands (don't block GUI thread)
- Progress signal emission for long operations
- Error signal emission with recovery options
- Session state synchronization

#### 2. **Functional Screen Implementations** (CRITICAL)

**Home Screen:**

- [ ] Recent investigations list (load from storage)
- [ ] New investigation button → file browser dialog
- [ ] Open investigation → load session
- [ ] Settings access

**Observe Screen:**

- [ ] Directory/file tree browser
- [ ] Eye selection checkboxes (file_sight, import_sight, etc.)
- [ ] Start observation button
- [ ] Real-time progress bar
- [ ] Results viewer (structured observation display)
- [ ] Export observation button

**Investigate Screen:**

- [ ] Investigation configuration panel
- [ ] Query type selector (structure, connections, anomalies, etc.)
- [ ] Focus path input
- [ ] Execute investigation button
- [ ] Results display with filtering
- [ ] Pattern visualization

**Patterns Screen:**

- [ ] Pattern library browser (builtin + custom)
- [ ] Category filters (security, performance, style, architecture)
- [ ] Scan configuration (path, scope, categories)
- [ ] Execute scan button
- [ ] Match results with context
- [ ] Export results

**Export Screen:**

- [ ] Format selector (JSON, Markdown, HTML, CSV, PDF, SVG, Jupyter)
- [ ] Session/investigation selector
- [ ] Output path with file dialog
- [ ] Include options (evidence, patterns, notes)
- [ ] Export preview
- [ ] Execute export with progress

#### 3. **Session Management** (HIGH)

- [ ] Auto-save current session every 30 seconds
- [ ] Recent investigations list (last 10)
- [ ] Session recovery on crash
- [ ] Session metadata display (created, modified, file count)

#### 4. **Error Handling & User Feedback** (CRITICAL)

- [ ] Try-catch around ALL bridge command calls
- [ ] QMessageBox for errors with:
  - Clear error message
  - Context (what was being attempted)
  - Suggested recovery action
  - Option to view details/logs
- [ ] Success notifications (QSystemTrayIcon or status bar)
- [ ] Progress dialogs with cancel buttons for long operations

#### 5. **Packaging and Runtime Docs**

- [ ] PySide6 installation guidance for Windows/Linux/macOS
- [ ] Troubleshooting guide for common GUI issues
- [ ] Distribution packages (.dmg, .exe, .AppImage) - **v2.1.1**

### Acceptance Criteria (Revised)

#### Must Have (v2.1.0 Release Blockers)

- [ ] `codemarshal gui` launches successfully with PySide6 installed
- [ ] **Home Screen:** Can browse and open recent investigations
- [ ] **Observe Screen:** Can select path, choose eyes, run observation, view results
- [ ] **Investigate Screen:** Can configure and run investigation, view results
- [ ] **Patterns Screen:** Can browse patterns, run scan, view matches
- [ ] **Export Screen:** Can select format and export results
- [ ] All screens handle errors gracefully with user-friendly messages
- [ ] Progress shown for all operations > 2 seconds
- [ ] Application doesn't crash on any user action
- [ ] Documentation complete

#### Should Have (v2.1.0)

- [ ] Keyboard shortcuts for common actions
- [ ] Session auto-save
- [ ] Results filtering and search
- [ ] Export preview

#### Nice to Have (v2.2.0)

- [ ] Native distribution packages
- [ ] Plugin UI
- [ ] Real-time file watching
- [ ] Split views

### Risk Assessment (Revised)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GUI-Engine integration complexity | **High** | **Critical** | Design integration layer before coding; pair programming |
| PySide6 threading issues | **High** | **High** | Use QThreadPool for all bridge calls; extensive testing |
| Current placeholder architecture unsuitable | **Medium** | **High** | Review architecture before implementation; refactor if needed |
| Cross-platform UI inconsistencies | **High** | **Medium** | Test early on all platforms; use Qt stylesheets |
| Performance with large codebases | **Medium** | **Medium** | Implement lazy loading; pagination; background threads |
| Scope creep | **High** | **High** | Strict scope enforcement; defer non-critical features |
| Developer availability | **Medium** | **High** | Require 2 developers minimum; knowledge sharing |

**Overall Risk Level:** **HIGH**  
**Mitigation Strategy:**

- Complete integration design before implementation
- Daily standups to catch blockers early
- Weekly demos to validate progress
- Aggressive scope cutting for v2.1.0

---

## Technical Debt Items (Address in v2.1.0 or v2.1.1)

### Must Fix (v2.1.0)

- [ ] **pyproject.toml version:** Update from 2.0.0 to 2.1.0
- [ ] **GUI-Engine integration:** Complete bridge implementation
- [ ] **Error handling:** All bridge calls wrapped in try-catch

### Should Fix (v2.1.1)

- [ ] **anchors.py TODO:** Implement IMPORT_SIGNATURE content fingerprinting
- [ ] **recovery/restore.py TODO:** Replace hardcoded version with package metadata
- [ ] **recovery/backup.py TODOs:** Implement incremental backup; fix version
- [ ] **shutdown.py TODOs:** Integrate with storage.atomic and integrity.recovery

### Nice to Fix (v2.2.0)

- [ ] **invariants_test.py TODOs:** Implement actual constitutional compliance tests
- [ ] **Core TODOs:** Address remaining TODOs in critical path

---

## Execution Order (Revised)

### Week 1 (Feb 13-19): Foundation & Design

- **Day 1:** Fix pyproject.toml version; audit current GUI architecture
- **Day 2:** Design GUI-Engine integration layer
- **Day 3:** Implement GUICommandBridge with async support
- **Day 4:** Implement session state management
- **Day 5:** Home Screen v2 with recent investigations
- **Weekend:** Code review and architecture validation

### Week 2 (Feb 20-26): Observe & Investigate Screens

- **Day 1-2:** Observe Screen - file browser, eye selection
- **Day 3:** Observe Screen - progress, results viewer
- **Day 4-5:** Investigate Screen - configuration, query interface
- **Weekend:** Integration testing

### Week 3 (Feb 27-Mar 5): Patterns & Export Screens

- **Day 1-2:** Patterns Screen - library browser, scan execution
- **Day 3-4:** Export Screen - format selection, preview, execution
- **Day 5:** Error handling implementation across all screens
- **Weekend:** Initial end-to-end testing

### Week 4 (Mar 6-12): Polish & Testing

- **Day 1-2:** Progress indicators and cancellation support
- **Day 3:** Keyboard navigation and accessibility
- **Day 4-5:** Integration testing and bug fixes
- **Weekend:** Cross-platform testing

### Week 5 (Mar 13-19): Documentation & Validation

- **Day 1-2:** GUI user guide
- **Day 3:** Troubleshooting documentation
- **Day 4:** Packaging and distribution docs
- **Day 5:** Final validation and acceptance testing

### Week 6 (Mar 20-22): Release

- **Day 1-2:** Release preparation
- **Day 3:** v2.1.0 release

---

## Done Definition for v2.1.0 (Revised)

v2.1.0 is considered complete when:

1. **All CRITICAL acceptance criteria met** (see above checklist)
2. **GUI-Engine integration fully functional:**
   - All bridge commands callable from GUI
   - Async execution (no GUI freezing)
   - Proper error handling
3. **Full test/coverage gates remain green:**
   - All 168+ tests passing
   - Coverage ≥ 90% (currently 96.56%)
   - GUI tests passing on CI with PySide6
4. **Documentation complete:**
   - GUI installation instructions
   - User guide for all five screens
   - Troubleshooting section
   - API documentation updated
5. **No critical or high-priority bugs**
6. **CHANGELOG.md updated**
7. **Release notes published**

---

## Post-v2.1 Roadmap

### v2.1.1 (Maintenance Release - 2 weeks after v2.1.0)

- [ ] Fix pyproject.toml version mismatch
- [ ] Implement TODOs in anchors.py, recovery, backup, shutdown
- [ ] Performance optimizations
- [ ] Bug fixes from v2.1.0 feedback

### v2.2.0 (Feature Release - 6-8 weeks after v2.1.0)

- [ ] Native distribution packages (.dmg, .exe, .AppImage)
- [ ] Advanced GUI features (split views, tabs, docking)
- [ ] Real-time file watching with auto-refresh
- [ ] Investigation comparison tools
- [ ] Custom pattern editor UI
- [ ] Plugin marketplace UI

### v3.0.0 (Major Release - Long-term)

- [ ] Cloud sync for investigations (opt-in, encrypted)
- [ ] Team collaboration features
- [ ] Advanced visualization (3D dependency graphs)
- [ ] AI-assisted pattern detection (local-only)
- [ ] Mobile companion app (view-only)

---

## Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Detailed version history
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - Command usage and workflows
- [docs/FEATURES.md](docs/FEATURES.md) - Implemented features and phase mapping
- [docs/architecture.md](docs/architecture.md) - System architecture documentation
- [docs/index.md](docs/index.md) - Documentation navigation
- [README.md](README.md) - Project overview

---

## Contributing to Phase 5

**⚠️ IMPORTANT:** Before contributing to Phase 5, read this entire document.

To contribute:

1. Review the **Critical Issues** section above
2. Understand the **GUI-Engine Integration** requirements
3. Check existing GUI code in `desktop/` directory
4. Follow the architecture in `docs/architecture.md` Interface Layer section
5. Ensure all GUI features maintain CLI parity
6. Add tests for new GUI functionality
7. Update documentation

**Contact:** Open an issue with tag `phase-5` for coordination.

---

**Questions or concerns about the roadmap?**  
Open an issue with the `roadmap` tag for discussion.

**Last Updated:** February 13, 2026  
**Next Review:** February 20, 2026
