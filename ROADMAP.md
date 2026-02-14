# CodeMarshal Roadmap (Execution Status)

**Version:** 2.1.1-dev  
**Last Updated:** February 14, 2026  
**Current Focus:** v2.1.1 Maintenance - Reliability Hardening

---

## Summary

All roadmap phases `0-9` are complete, including the desktop GUI (Phase 5).  
Current work is maintenance hardening for backup/restore reliability, shutdown integrity, and documentation truth-sync.

---

## Phase Status

| Phase | Name                            | Status   | Evidence                                                                    |
| ----- | ------------------------------- | -------- | --------------------------------------------------------------------------- |
| 0     | Foundation Repair               | Complete | Import-chain fixes landed; test discovery stabilized                        |
| 1     | Pattern System Renaissance      | Complete | Built-in pattern libraries + engine/dashboard support present               |
| 2     | Inquiry Engine Expansion        | Complete | Extended analyzer behavior for structure/connections/anomalies              |
| 3     | Multi-Language Support          | Complete | JS/TS, Java, Go sights + language detector                                  |
| 4     | IDE Integration Suite           | Complete | VS Code / Neovim / JetBrains foundations in repo                            |
| 5     | Desktop GUI                     | Complete | PySide6 GUI bridge/session/screens implemented with dedicated desktop tests |
| 6     | Storage & Data Layer            | Complete | Migration, transactional storage, knowledge base scaffolding                |
| 7     | Test Suite Completion           | Complete | Full suite passing; coverage gate exceeded                                  |
| 8     | Advanced Export & Visualization | Complete | Jupyter, PDF, SVG exporters + tests                                         |
| 9     | Plugin System                   | Complete | Plugin API and loader foundations                                           |

---

## Latest Validation Snapshot (February 14, 2026)

- Full suite with GUI dependency (PySide6 in `venv`): `186 passed, 2 skipped`
- Coverage with GUI dependency: `95.70%` (gate: `90%`)
- Full suite without GUI dependency (system Python): `184 passed, 3 skipped`
- Coverage without GUI dependency: `93.99%` (gate: `90%`)
- `pyproject.toml` version: `2.1.0` (maintenance work tracks `2.1.1-dev`)

---

## Active v2.1.1 Maintenance Priorities

- Recovery payload compatibility (`snapshot`/`observations`) and deterministic integrity hashing
- Incremental backup chain materialization in restore paths
- Package-version metadata wiring in backup/restore checkpoints
- Shutdown integration with `storage.atomic` and corruption checks
- Import-signature anchor generator implementation
- Targeted invariant guardrails and CI GUI smoke coverage

---

## Historical Planning Archive

The following Phase 5 planning section is preserved for historical traceability.

## Archived: Revised Phase 5 Desktop GUI Implementation

### Objective

Transform the current GUI shell into a production-ready desktop interface that provides full CLI parity through PySide6.

### Revised Timeline & Milestones

**Original Estimate:** 4 weeks (Feb 13 - Mar 8)  
**Revised Estimate:** 6 weeks (Feb 13 - Mar 22)  
**Reason:** GUI currently has zero functionality; requires complete implementation, not just "productization"

| Milestone                  | Target Date  | Deliverable                                              | Priority      | Status      |
| -------------------------- | ------------ | -------------------------------------------------------- | ------------- | ----------- |
| **Phase 5A: Foundation**   |              |                                                          |               |             |
| Fix Version Number         | Feb 13, 2026 | Update pyproject.toml to 2.1.0                           | ðŸ”´ Critical | Not Started |
| GUI-Engine Bridge          | Feb 14, 2026 | Integration layer between Qt signals and bridge commands | ðŸ”´ Critical | Not Started |
| Session State Management   | Feb 15, 2026 | Recent investigations, session restore, auto-save        | ðŸŸ  High     | Not Started |
| **Phase 5B: Core Screens** |              |                                                          |               |             |
| Home Screen v2             | Feb 17, 2026 | Project browser, recent list, new investigation flow     | ðŸŸ  High     | Not Started |
| Observe Screen             | Feb 20, 2026 | File browser, eye selection, real-time progress, results | ðŸ”´ Critical | Not Started |
| Investigate Screen         | Feb 24, 2026 | Investigation config, query interface, pattern results   | ðŸ”´ Critical | Not Started |
| Patterns Screen            | Feb 27, 2026 | Pattern library, scan execution, match visualization     | ðŸŸ  High     | Not Started |
| Export Screen              | Mar 2, 2026  | Format selection, preview, progress, file dialogs        | ðŸŸ  High     | Not Started |
| **Phase 5C: Polish**       |              |                                                          |               |             |
| Error Handling             | Mar 4, 2026  | Try-catch all bridge calls, user-friendly dialogs        | ðŸ”´ Critical | Not Started |
| Progress Indicators        | Mar 5, 2026  | Progress bars for long operations, cancellation support  | ðŸŸ  High     | Not Started |
| Keyboard Navigation        | Mar 6, 2026  | Tab order, shortcuts, accessibility                      | ðŸŸ¡ Medium   | Not Started |
| **Phase 5D: Validation**   |              |                                                          |               |             |
| Integration Testing        | Mar 8, 2026  | End-to-end workflows, error scenarios                    | ðŸŸ  High     | Not Started |
| Cross-Platform Testing     | Mar 10, 2026 | Windows, Linux, macOS validation                         | ðŸŸ  High     | Not Started |
| Documentation              | Mar 12, 2026 | GUI user guide, troubleshooting, packaging               | ðŸŸ¡ Medium   | Not Started |
| **Phase 5E: Release**      |              |                                                          |               |             |
| v2.1.0 Release             | Mar 15, 2026 | All acceptance criteria met                              | ðŸŸ  High     | Not Started |

### Resource Requirements (Revised)

| Resource       | Requirement          | Notes                                    |
| -------------- | -------------------- | ---------------------------------------- |
| Development    | 2 developers minimum | PySide6/Qt experience **required**       |
| Architecture   | Senior review        | Bridge-Engine-GUI integration design     |
| Testing        | QA validation        | Cross-platform testing (Win/Linux/macOS) |
| Documentation  | Technical writer     | GUI-specific user guides                 |
| Infrastructure | CI updates           | GUI testing in headless environments     |

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
- [ ] New investigation button â†’ file browser dialog
- [ ] Open investigation â†’ load session
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

| Risk                                        | Probability | Impact       | Mitigation                                                    |
| ------------------------------------------- | ----------- | ------------ | ------------------------------------------------------------- |
| GUI-Engine integration complexity           | **High**    | **Critical** | Design integration layer before coding; pair programming      |
| PySide6 threading issues                    | **High**    | **High**     | Use QThreadPool for all bridge calls; extensive testing       |
| Current placeholder architecture unsuitable | **Medium**  | **High**     | Review architecture before implementation; refactor if needed |
| Cross-platform UI inconsistencies           | **High**    | **Medium**   | Test early on all platforms; use Qt stylesheets               |
| Performance with large codebases            | **Medium**  | **Medium**   | Implement lazy loading; pagination; background threads        |
| Scope creep                                 | **High**    | **High**     | Strict scope enforcement; defer non-critical features         |
| Developer availability                      | **Medium**  | **High**     | Require 2 developers minimum; knowledge sharing               |

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

## GUI Implementation Architecture

### GUI-Engine Integration Layer

We need a bridge layer to connect Qt signals/slots with the existing bridge commands:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    GUI Layer (PySide6)                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚  â”‚ Home    â”‚ â”‚ Observe  â”‚ â”‚Investigateâ”‚ â”‚ Patterns    â”‚ â”‚
â”‚  â”‚ View    â”‚ â”‚ View     â”‚ â”‚ View     â”‚ â”‚ View        â”‚ â”‚
â”‚  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”‚       â”‚           â”‚            â”‚              â”‚         â”‚
â”‚  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚  â”‚              GUI Controller                          â”‚ â”‚
â”‚  â”‚  â€¢ Signal/slot connections                           â”‚ â”‚
â”‚  â”‚  â€¢ Form validation                                   â”‚ â”‚
â”‚  â”‚  â€¢ State management                                  â”‚ â”‚
â”‚  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”‚       â”‚                                                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚  GUICommandBridgeâ”‚â—„â”€â”€â–ºâ”‚      Worker Threads      â”‚    â”‚
â”‚  â”‚  â€¢ Async wrapper â”‚    â”‚  (QThreadPool)           â”‚    â”‚
â”‚  â”‚  â€¢ Progress      â”‚    â”‚  â€¢ Non-blocking bridge   â”‚    â”‚
â”‚  â”‚  â€¢ Error handlingâ”‚    â”‚    commands              â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â”‚       â”‚                                                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                Bridge Layer (Existing)                   â”‚
â”‚         (investigate, observe, query, etc.)              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Core Components

#### 1. GUICommandBridge (`desktop/core/command_bridge.py`)

**Responsibilities:**

- Async execution of bridge commands using `QThreadPool`
- Signal emission for progress updates (every 100ms)
- Error handling with recovery options
- Cancellation support via `QMutex`

**Key Methods:**

```python
class GUICommandBridge(QObject):
    # Signals
    observation_started = Signal(str)
    observation_progress = Signal(int, int)  # current, total
    observation_complete = Signal(dict)
    observation_error = Signal(str, str)

    # Async methods
    async def run_observation(self, path: Path, eye_types: List[str])
    async def run_investigation(self, path: Path, scope: str, intent: str)
    async def run_pattern_scan(self, path: Path, categories: List[str])
    async def run_export(self, session_id: str, format: str, output: Path)
```

#### 2. Session Manager (`desktop/core/session_manager.py`)

**Responsibilities:**

- Auto-save current session every 30 seconds
- Load/save recent investigations list
- Session recovery on crash
- Track dirty state (unsaved changes)

#### 3. Worker Threads (`desktop/core/worker.py`)

**Responsibilities:**

- Wrap bridge commands in `QRunnable`
- Handle thread lifecycle
- Report progress back to GUI
- Handle cancellation requests

---

## Screen-by-Screen Implementation Details

### Phase 1: Foundation Components (Week 1)

#### GUICommandBridge Implementation

```python
# desktop/core/command_bridge.py
from PySide6.QtCore import QObject, Signal, QThreadPool, QRunnable
from typing import Any, Callable
import asyncio

class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str, str)
    progress = Signal(int, int)

class BridgeWorker(QRunnable):
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(type(e).__name__, str(e))

    def cancel(self):
        self._is_cancelled = True

class GUICommandBridge(QObject):
    observation_started = Signal(str)
    observation_progress = Signal(int, int)
    observation_complete = Signal(dict)
    observation_error = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.active_workers = []

    def run_observation(self, path: Path, eye_types: List[str]):
        """Start observation in background thread."""
        self.observation_started.emit(str(path))

        worker = BridgeWorker(
            self._execute_observation,
            path, eye_types
        )
        worker.signals.finished.connect(self.observation_complete.emit)
        worker.signals.error.connect(self.observation_error.emit)
        worker.signals.progress.connect(self.observation_progress.emit)

        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def _execute_observation(self, path: Path, eye_types: List[str]):
        # Call existing bridge command
        from bridge.commands.observe import execute_observation, ObservationRequest, ObservationType

        request = ObservationRequest(
            types={ObservationType(t) for t in eye_types},
            target_path=path,
            session_id=self._get_current_session_id()
        )

        return execute_observation(request)
```

---

### Phase 2: Home Screen (Week 1-2)

**Current State:** Navigation buttons only  
**Target State:** Full project browser with recent investigations

#### Implementation

**File:** `desktop/views/home.py` (update existing)

**Key Features:**

1. **Recent Investigations Panel**
   - Load from `storage.investigation_storage`
   - Display: name, date, path, file count
   - Actions: open, delete, export
   - Limit to last 10 investigations

2. **New Investigation Flow**
   - "New Investigation" button â†’ `QFileDialog.getExistingDirectory()`
   - Quick actions: "Observe Current Directory", "Pattern Scan Recent Project"
   - Remember last used path

3. **Settings Access**
   - Button to open settings dialog
   - Theme toggle (dark/light)
   - Default export format selection
   - Storage location configuration

```python
class HomeView(QtWidgets.QWidget):
    """Enhanced home view with recent investigations."""

    navigate_requested = Signal(str)
    investigation_opened = Signal(str)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager()
        self._build_ui()
        self._load_recent_investigations()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Title section
        title = QtWidgets.QLabel("CodeMarshal")
        title.setObjectName("title")
        layout.addWidget(title, alignment=QtCore.Qt.AlignHCenter)

        # Recent investigations
        recent_group = QtWidgets.QGroupBox("Recent Investigations")
        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_investigation_selected)
        recent_layout = QtWidgets.QVBoxLayout(recent_group)
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_group)

        # Quick actions
        actions_group = QtWidgets.QGroupBox("Quick Actions")
        actions_layout = QtWidgets.QHBoxLayout(actions_group)

        new_btn = QtWidgets.QPushButton("New Investigation")
        new_btn.clicked.connect(self._on_new_investigation)
        actions_layout.addWidget(new_btn)

        observe_btn = QtWidgets.QPushButton("Quick Observe")
        observe_btn.clicked.connect(lambda: self.navigate_requested.emit("observe"))
        actions_layout.addWidget(observe_btn)

        layout.addWidget(actions_group)

    def _load_recent_investigations(self):
        """Load and display recent investigations."""
        investigations = self.session_manager.get_recent_investigations(limit=10)
        self.recent_list.clear()

        for inv in investigations:
            item = QtWidgets.QListWidgetItem()
            item.setText(f"{inv['name']} - {inv['path']}")
            item.setData(QtCore.Qt.UserRole, inv['session_id'])
            item.setToolTip(f"Created: {inv['created']}\nFiles: {inv['file_count']}")
            self.recent_list.addItem(item)

    def _on_new_investigation(self):
        """Open file dialog for new investigation."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Investigate",
            self.session_manager.get_last_path()
        )
        if path:
            self.session_manager.set_last_path(path)
            self.navigate_requested.emit("investigate")
```

---

### Phase 3: Observe Screen (Week 2)

**Current State:** Single label  
**Target State:** Full observation workflow

#### Layout Design

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Path: [/home/user/project] [Browse]                 â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Eyes: â˜‘ File  â˜‘ Import  â˜‘ Export  â˜ Boundary       â”‚
â”‚      â˜ Encoding  [Select All] [Clear All]          â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Run Observation]          Progress: [â–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘] 67%  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Results:                                             â”‚
â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚ â”‚ ðŸ“ src/ (42 files)                               â”‚ â”‚
â”‚ â”‚   ðŸ“„ main.py (12 imports, 5 exports)            â”‚ â”‚
â”‚ â”‚   ðŸ“„ utils.py (3 imports, 8 exports)            â”‚ â”‚
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Export] [View Details] [Clear]                     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Implementation

**File:** `desktop/views/observe.py` (rewrite)

```python
class ObserveView(QtWidgets.QWidget):
    """Complete observation workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_bridge = GUICommandBridge()
        self._setup_signals()
        self._build_ui()

    def _setup_signals(self):
        """Connect command bridge signals."""
        self.command_bridge.observation_started.connect(self._on_observation_started)
        self.command_bridge.observation_progress.connect(self._on_observation_progress)
        self.command_bridge.observation_complete.connect(self._on_observation_complete)
        self.command_bridge.observation_error.connect(self._on_observation_error)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Path selection
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(QtWidgets.QLabel("Path:"))
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Select directory to observe...")
        path_layout.addWidget(self.path_input)

        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Eye selection
        eyes_group = QtWidgets.QGroupBox("Observation Eyes")
        eyes_layout = QtWidgets.QGridLayout(eyes_group)

        self.eye_checkboxes = {}
        eyes = [
            ("file_sight", "File Structure"),
            ("import_sight", "Imports"),
            ("export_sight", "Exports"),
            ("boundary_sight", "Boundaries"),
            ("encoding_sight", "Encoding"),
        ]

        for i, (eye_id, eye_name) in enumerate(eyes):
            checkbox = QtWidgets.QCheckBox(eye_name)
            checkbox.setChecked(True)  # Default to selected
            checkbox.setToolTip(f"Observe {eye_name.lower()}")
            self.eye_checkboxes[eye_id] = checkbox
            eyes_layout.addWidget(checkbox, i // 3, i % 3)

        # Select All / Clear All buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_eyes)
        clear_all_btn = QtWidgets.QPushButton("Clear All")
        clear_all_btn.clicked.connect(self._clear_all_eyes)
        buttons_layout.addWidget(select_all_btn)
        buttons_layout.addWidget(clear_all_btn)
        buttons_layout.addStretch()
        eyes_layout.addLayout(buttons_layout, 2, 0, 1, 3)

        layout.addWidget(eyes_group)

        # Run button and progress
        action_layout = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton("Run Observation")
        self.run_btn.clicked.connect(self._on_run_observation)
        action_layout.addWidget(self.run_btn)

        action_layout.addStretch()
        action_layout.addWidget(QtWidgets.QLabel("Progress:"))
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        action_layout.addWidget(self.progress_bar)

        layout.addLayout(action_layout)

        # Results viewer
        results_group = QtWidgets.QGroupBox("Results")
        self.results_tree = QtWidgets.QTreeWidget()
        self.results_tree.setHeaderLabels(["Item", "Details"])
        results_layout = QtWidgets.QVBoxLayout(results_group)
        results_layout.addWidget(self.results_tree)
        layout.addWidget(results_group)

        # Action buttons
        bottom_layout = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton("Export")
        export_btn.clicked.connect(self._on_export)
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)
        bottom_layout.addWidget(export_btn)
        bottom_layout.addWidget(clear_btn)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def _on_browse(self):
        """Open file browser dialog."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Directory"
        )
        if path:
            self.path_input.setText(path)

    def _on_run_observation(self):
        """Start observation with error handling."""
        path = Path(self.path_input.text())

        # Validation
        if not path.exists():
            QtWidgets.QMessageBox.critical(
                self,
                "Invalid Path",
                f"The path '{path}' does not exist."
            )
            return

        # Get selected eyes
        selected_eyes = [
            eye_id for eye_id, checkbox in self.eye_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_eyes:
            QtWidgets.QMessageBox.warning(
                self,
                "No Eyes Selected",
                "Please select at least one observation eye."
            )
            return

        # Disable UI during operation
        self.run_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # Start observation
        self.command_bridge.run_observation(path, selected_eyes)

    def _on_observation_complete(self, results: dict):
        """Display observation results."""
        self.run_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        # Clear previous results
        self.results_tree.clear()

        # Populate tree with results
        if "observations" in results:
            for obs in results["observations"]:
                item = QtWidgets.QTreeWidgetItem([
                    obs.get("path", "Unknown"),
                    f"{obs.get('file_count', 0)} files"
                ])
                self.results_tree.addTopLevelItem(item)

    def _on_observation_error(self, error_type: str, message: str):
        """Handle observation errors."""
        self.run_btn.setEnabled(True)

        QtWidgets.QMessageBox.critical(
            self,
            f"Observation Failed - {error_type}",
            f"Could not complete observation:\n\n{message}\n\n"
            f"Try reducing scope or checking file permissions."
        )
```

---

### Phase 4: Investigate Screen (Week 2-3)

**Current State:** Single label  
**Target State:** Investigation configuration and results

#### Layout Design

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Investigation Configuration                          â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Target: [/home/user/project] [Browse]               â”‚
â”‚ Scope: (â€¢) File  ( ) Module  ( ) Package  ( ) Codebaseâ”‚
â”‚ Intent: [Initial Scan          â–¼]                   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Query Configuration                                  â”‚
â”‚ Question Type: [Structure â–¼]                        â”‚
â”‚ Focus: [________] [Optional]                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Start Investigation]     [Save for Later]          â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Results:                                             â”‚
â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚ â”‚ Structure Analysis:                              â”‚ â”‚
â”‚ â”‚ â€¢ 42 files across 8 directories                 â”‚ â”‚
â”‚ â”‚ â€¢ 156 imports, 89 exports                       â”‚ â”‚
â”‚ â”‚ â€¢ Average file size: 4.2 KB                     â”‚ â”‚
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Implementation

**File:** `desktop/views/investigate.py` (rewrite)

```python
class InvestigateView(QtWidgets.QWidget):
    """Complete investigation workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_bridge = GUICommandBridge()
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Investigation configuration
        config_group = QtWidgets.QGroupBox("Investigation Configuration")
        config_layout = QtWidgets.QFormLayout(config_group)

        # Target path
        path_layout = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        config_layout.addRow("Target:", path_layout)

        # Scope selection
        self.scope_group = QtWidgets.QButtonGroup(self)
        scope_layout = QtWidgets.QHBoxLayout()
        for scope in ["File", "Module", "Package", "Codebase"]:
            radio = QtWidgets.QRadioButton(scope)
            self.scope_group.addButton(radio)
            scope_layout.addWidget(radio)
        config_layout.addRow("Scope:", scope_layout)

        # Intent dropdown
        self.intent_combo = QtWidgets.QComboBox()
        self.intent_combo.addItems([
            "Initial Scan",
            "Deep Analysis",
            "Architecture Review",
            "Security Audit",
            "Performance Review"
        ])
        config_layout.addRow("Intent:", self.intent_combo)

        layout.addWidget(config_group)

        # Query configuration
        query_group = QtWidgets.QGroupBox("Query Configuration")
        query_layout = QtWidgets.QFormLayout(query_group)

        self.question_type = QtWidgets.QComboBox()
        self.question_type.addItems([
            "Structure",
            "Purpose",
            "Connections",
            "Anomalies",
            "Thinking"
        ])
        query_layout.addRow("Question Type:", self.question_type)

        self.focus_input = QtWidgets.QLineEdit()
        self.focus_input.setPlaceholderText("Optional path or pattern to focus on")
        query_layout.addRow("Focus:", self.focus_input)

        layout.addWidget(query_group)

        # Action buttons
        action_layout = QtWidgets.QHBoxLayout()
        start_btn = QtWidgets.QPushButton("Start Investigation")
        start_btn.clicked.connect(self._on_start)
        save_btn = QtWidgets.QPushButton("Save for Later")
        save_btn.clicked.connect(self._on_save)
        action_layout.addWidget(start_btn)
        action_layout.addWidget(save_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Results area
        results_group = QtWidgets.QGroupBox("Results")
        self.results_text = QtWidgets.QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout = QtWidgets.QVBoxLayout(results_group)
        results_layout.addWidget(self.results_text)
        layout.addWidget(results_group)
```

---

### Phase 5: Patterns Screen (Week 3-4)

**Current State:** Single label  
**Target State:** Pattern library and scanning

#### Layout Design

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Pattern Library                          [Refresh]  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Categories: [All â–¼]  Search: [________]            â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â˜‘ Security (8 patterns)                             â”‚
â”‚   â€¢ hardcoded_credentials                           â”‚
â”‚   â€¢ sql_injection_risk                              â”‚
â”‚ â˜‘ Performance (20 patterns)                         â”‚
â”‚   â€¢ nested_loops                                    â”‚
â”‚   â€¢ synchronous_io                                  â”‚
â”‚ â˜‘ Style (15 patterns)                               â”‚
â”‚ â˜‘ Architecture (12 patterns)                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Scan Configuration                                   â”‚
â”‚ Path: [/home/user/project] [Browse]                 â”‚
â”‚ [Run Pattern Scan]        Progress: [Ready]         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Results:                                             â”‚
â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚ â”‚ ðŸ”´ Critical: 2 matches                           â”‚ â”‚
â”‚ â”‚   hardcoded_credentials @ src/config.py:42      â”‚ â”‚
â”‚ â”‚ ðŸŸ¡ Warnings: 5 matches                           â”‚ â”‚
â”‚ â”‚   nested_loops @ src/process.py:89              â”‚ â”‚
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

### Phase 6: Export Screen (Week 4)

**Current State:** Single label  
**Target State:** Complete export workflow

#### Layout Design

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Export Configuration                                 â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Source: [Recent Investigation â–¼]                    â”‚
â”‚         "investigation_20260213_123456"             â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Format: (â€¢) JSON  ( ) Markdown  ( ) HTML           â”‚
â”‚        ( ) CSV    ( ) PDF       ( ) SVG            â”‚
â”‚        ( ) Jupyter Notebook                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Include: â˜‘ Evidence  â˜‘ Patterns  â˜‘ Notes           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Output: [/home/user/export.md] [Browse]            â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Preview] [Export]        Status: [Ready]          â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Preview:                                             â”‚
â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚ â”‚ ## Investigation Report                          â”‚ â”‚
â”‚ â”‚ Generated: 2026-02-13 14:30                      â”‚ â”‚
â”‚ â”‚ ...                                              â”‚ â”‚
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## File Structure

```
desktop/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ app.py                    # Update: Main window with navigation
â”œâ”€â”€ theme.py                  # Already exists
â”œâ”€â”€ core/                     # NEW: Integration layer
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ command_bridge.py     # Async bridge to bridge commands
â”‚   â”œâ”€â”€ session_manager.py    # Session persistence
â”‚   â””â”€â”€ worker.py             # QThreadPool workers
â”œâ”€â”€ views/                    # UPDATE: Replace placeholders
â”‚   â”œâ”€â”€ __init__.py           # Update exports
â”‚   â”œâ”€â”€ home.py              # UPDATE: Add recent investigations
â”‚   â”œâ”€â”€ observe.py           # UPDATE: Full implementation
â”‚   â”œâ”€â”€ investigate.py       # UPDATE: Full implementation
â”‚   â”œâ”€â”€ patterns.py          # UPDATE: Full implementation
â”‚   â”œâ”€â”€ export.py            # UPDATE: Full implementation
â”‚   â””â”€â”€ widgets/             # NEW: Reusable components
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ file_browser.py
â”‚       â”œâ”€â”€ progress_dialog.py
â”‚       â”œâ”€â”€ results_viewer.py
â”‚       â””â”€â”€ error_dialog.py
â””â”€â”€ tests/                   # NEW: GUI tests
    â”œâ”€â”€ __init__.py
    â”œâ”€â”€ test_command_bridge.py
    â”œâ”€â”€ test_session_manager.py
    â””â”€â”€ test_views/
        â”œâ”€â”€ test_home.py
        â”œâ”€â”€ test_observe.py
        â””â”€â”€ ...
```

---

## Risk Mitigation

| Risk                            | Mitigation                                               |
| ------------------------------- | -------------------------------------------------------- |
| Threading issues                | Use QThreadPool exclusively, never block GUI thread      |
| Memory leaks                    | Profile with memory_profiler, use weakrefs for callbacks |
| Cross-platform UI               | Test on all platforms weekly, use Qt stylesheets         |
| Performance with large projects | Implement lazy loading, pagination, virtual lists        |
| Bridge API changes              | Abstract bridge calls in command_bridge.py               |

---

## Success Criteria

### Must Have (Release Blockers)

- [ ] All 5 screens fully functional
- [ ] All bridge commands callable from GUI
- [ ] No GUI freezing during operations
- [ ] Comprehensive error handling
- [ ] Progress indicators for long operations
- [ ] Session auto-save and recovery
- [ ] 80% test coverage for desktop/ module

### Should Have

- [ ] Keyboard shortcuts
- [ ] Export preview
- [ ] Results filtering
- [ ] Recent investigations list

### Nice to Have

- [ ] Drag-and-drop file support
- [ ] Customizable layouts
- [ ] Plugin UI hooks

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
   - Coverage â‰¥ 90% (currently 96.56%)
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

**âš ï¸ IMPORTANT:** Before contributing to Phase 5, read this entire document.

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
