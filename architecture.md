# CodeMarshal Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** February 5, 2026  
**Document Type:** Architectural Reference

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architectural Philosophy](#architectural-philosophy)
3. [System Overview](#system-overview)
4. [Layer-by-Layer Architecture](#layer-by-layer-architecture)
   - [Layer 1: Observations (What Exists)](#layer-1-observations-what-exists)
   - [Layer 2: Inquiry (Questions & Patterns)](#layer-2-inquiry-questions--patterns)
   - [Layer 3: Interface (How We Look)](#layer-3-interface-how-we-look)
   - [Layer 4: Bridge (How We Interact)](#layer-4-bridge-how-we-interact)
   - [Layer 5: Core (Execution Spine)](#layer-5-core-execution-spine)
5. [Constitutional Framework](#constitutional-framework)
6. [Data Models & Storage](#data-models--storage)
7. [Command Execution Flows](#command-execution-flows)
8. [Boundary System](#boundary-system)
9. [Security Model](#security-model)
10. [Performance Considerations](#performance-considerations)
11. [Extension Points](#extension-points)
12. [Integration Patterns](#integration-patterns)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Appendix: File Reference](#appendix-file-reference)

---

## Executive Summary

CodeMarshal is a truth-preserving cognitive investigation environment designed to help humans understand complex codebases without introducing interpretation, inference, or opinion into the observation layer. The system operates on a fundamental principle: **separate what exists from how we understand it**.

The architecture follows a strict five-layer design where each layer has a single, well-defined responsibility:

1. **Observations Layer**: Immutable collection of facts from source code
2. **Inquiry Layer**: Human-guided questions and pattern analysis
3. **Interface Layer**: Presentation of information to users
4. **Bridge Layer**: Command execution and external integrations
5. **Core Layer**: Runtime authority and lifecycle management

This separation is enforced by a **boundary system** that prevents any layer from importing code from layers below its designated tier. Violations are detected at startup and cause immediate termination with detailed error reporting.

---

## Architectural Philosophy

### The Three Laws of CodeMarshal

CodeMarshal operates under three non-negotiable laws that govern every aspect of its design and implementation:

#### Law 1: Witness, Don't Interpret

The observation layer must only record what is textually present in source code. No inference, no guessing, no interpretation.

**Examples of what observations collect:**

- File paths, names, and sizes
- Import statements and their syntax
- Function and class signatures
- Comment text (not meaning)
- Code structure (not purpose)

**Examples of what observations MUST NOT collect:**

- Function purpose or behavior
- Code quality assessments
- Bug identification
- Performance implications
- Design pattern recognition (this belongs in Inquiry)

#### Law 2: Support, Don't Replace

The system exists to assist human investigation, not to replace human thinking. Every design decision reinforces human agency.

**Design implications:**

- Users must explicitly specify investigation scope
- No automatic analysis without user intent
- All findings are presented with evidence
- Users make conclusions, system provides data
- Questions drive investigation, not automatic reports

#### Law 3: Clarify, Don't Obscure

The interface must make reality clearer, not introduce ambiguity or confusion.

**Interface principles:**

- Single focus at any time
- Progressive disclosure of information
- Explicit rather than implicit behavior
- All limitations are documented
- Truth preservation is guaranteed

### The Observer Pattern Philosophy

CodeMarshal implements what can be called a **pure observer pattern** where:

- **Observations are immutable**: Once recorded, they cannot be modified
- **Evidence is hash-verified**: Every observation includes cryptographic proof
- **Provenance is tracked**: Every piece of information can be traced to its source
- **Limitations are declared**: Every observation explicitly states what it cannot see

---

## System Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   CLI (Bridge)  │  │   TUI (Bridge)  │  │     API (Bridge)            │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬─────────────────┘ │
└───────────┼────────────────────┼────────────────────────┼────────────────────┘
            │                    │                        │
            └────────────────────┼────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRIDGE LAYER (Layer 4)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   Commands      │  │  Coordination    │  │      Integrations            │ │
│  │  - investigate  │  │  - Scheduling    │  │      - Editor Plugins        │ │
│  │  - observe      │  │  - Caching       │  │      - CI/CD                 │ │
│  │  - query        │  │  - Session Mgmt  │  │      - Export Formats        │ │
│  │  - export       │  │                  │  │                             │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬─────────────────┘ │
└───────────┼────────────────────┼────────────────────────┼────────────────────┘
            │                    │                        │
            ▼                    ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INQUIRY LAYER (Layer 3)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │    Questions    │  │     Patterns    │  │      Notebook               │ │
│  │  - Structure    │  │  - Coupling     │  │      - Notes               │ │
│  │  - Connections  │  │  - Complexity   │  │      - Timeline            │ │
│  │  - Anomalies    │  │  - Density      │  │      - Export              │ │
│  │  - Purpose      │  │  - Uncertainty  │  │      - Constraints        │ │
│  │  - Thinking     │  │  - Violations   │  │                             │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬─────────────────┘ │
└───────────┼────────────────────┼────────────────────────┼────────────────────┘
            │                    │                        │
            ▼                    ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OBSERVATIONS LAYER (Layer 2)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │     Eyes        │  │     Record      │  │      Limitations           │ │
│  │  - File Sight   │  │  - Snapshot     │  │      - Declared           │ │
│  │  - Import Sight │  │  - Anchors      │  │      - Documented         │ │
│  │  - Export Sight │  │  - Integrity    │  │      - Validation         │ │
│  │  - Boundary     │  │  - Version      │  │      - Input Validation   │ │
│  │  - Encoding     │  │                 │  │                             │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬─────────────────┘ │
└───────────┼────────────────────┼────────────────────────┼────────────────────┘
            │                    │                        │
            ▼                    ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CORE LAYER (Layer 1)                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │    Runtime      │  │     Engine      │  │      State                   │ │
│  │  - Lifecycle    │  │  - Coordination │  │      - Phase Machine         │ │
│  │  - Context      │  │  - Layer Mgmt   │  │      - Transitions           │ │
│  │  - Constitution │  │  - Validation   │  │      - Recovery              │ │
│  │  - Shutdown     │  │                 │  │                             │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬─────────────────┘ │
└───────────┼────────────────────┼────────────────────────┼────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER (Shared)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  Investigations │  │   Snapshots      │  │      Metadata                │ │
│  │  - Sessions     │  │  - Observations   │  │      - Integrity Hashes      │ │
│  │  - History      │  │  - Anchors       │  │      - Version Info           │ │
│  │  - Recovery     │  │  - Patterns      │  │      - Configuration          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Information Flow

```
User Intent
    │
    ▼
┌──────────────┐
│ Command      │  1. Parse user intent
│ (Bridge)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Validation   │  2. Validate scope and permissions
│ (Bridge)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Runtime      │  3. Initialize context
│ (Core)       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Observations │  4. Collect facts (What exists?)
│ (Layer 2)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Snapshots    │  5. Record immutable evidence
│ (Storage)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Inquiry      │  6. Apply questions & patterns
│ (Layer 3)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Results      │  7. Present findings
│ (Interface)  │
└──────┬───────┘
       │
       ▼
User Understanding (Human makes conclusions)
```

---

## Layer-by-Layer Architecture

### Layer 1: Observations (What Exists)

The Observations layer is the foundation of CodeMarshal's truth-preserving approach. This layer is responsible for collecting immutable facts from source code without any interpretation or inference.

#### 1.1 Core Principles

**Immutability**

- Observations are recorded once and never modified
- Each observation includes a SHA256 hash for integrity verification
- Original source files are never altered
- Timestamps are recorded for provenance

**Purity**

- Only textually present information is collected
- No execution of code during observation
- No network access for observation collection
- No runtime state reflection

**Explicitness**

- Every limitation is declared upfront
- Confidence levels are never inferred
- Unknown states are explicitly marked
- Evidence is always provided

#### 1.2 The Eyes Subsystem

The Eyes subsystem contains different observation mechanisms, each responsible for a specific type of fact collection:

**File Sight (`observations/eyes/file_sight.py`)**

The File Sight observes filesystem structure and file metadata:

```
Responsibilities:
├── Directory tree traversal
├── File metadata collection (size, mtime, permissions)
├── File type detection
├── Symlink resolution and tracking
└── Binary vs text classification
```

**Key Classes:**

```python
class FileSight(AbstractEye):
    """
    Observes filesystem structure without interpretation.

    Constitutional Compliance:
    - Only collects what exists
    - No file content reading (use Export Sight for that)
    - No interpretation of file purpose
    """

    def observe(self, path: Path, depth: int = -1) -> FileObservation:
        """
        Observe files and directories at given path.

        Args:
            path: Root path to observe
            depth: Maximum traversal depth (-1 for unlimited)

        Returns:
            FileObservation with collected facts
        """

    def get_capabilities(self) -> Dict[str, Any]:
        """Return observation capabilities and limitations."""
```

**Import Sight (`observations/eyes/import_sight.py`)**

The Import Sight observes static import statements:

```
Responsibilities:
├── Parse import statements (not execute)
├── Identify imported modules
├── Track import types (static, from, relative)
├── Build dependency graph
└── Record import locations (file and line number)
```

**Key Classes:**

```python
class ImportSight(AbstractEye):
    """
    Observes static import statements without execution.

    Constitutional Compliance:
    - Parses syntax only, does not evaluate
    - Records what is imported, not what it means
    - No runtime dependency resolution
    """

    def observe(self, path: Path) -> ImportObservation:
        """Observe imports in Python files at given path."""

    def analyze_dependencies(self, observation: ImportObservation) -> DependencyGraph:
        """Analyze dependency relationships from observations."""
```

**Export Sight (`observations/eyes/export_sight.py`)**

The Export Sight observes what modules export:

```
Responsibilities:
├── Parse function/class definitions
├── Record signatures and decorators
├── Track module-level declarations
├── Identify public vs private symbols
└── Collect documentation comments (not meaning)
```

**Boundary Sight (`observations/eyes/boundary_sight.py`)**

The Boundary Sight observes module and package boundaries:

```
Responsibilities:
├── Identify package boundaries
├── Track __init__.py files
├── Detect circular dependencies
├── Monitor boundary crossings
└── Enforce architectural constraints
```

**Encoding Sight (`observations/eyes/encoding_sight.py`)**

The Encoding Sight detects file encodings and types:

```
Responsibilities:
├── Detect file encoding (UTF-8, ASCII, etc.)
├── Identify file types (text, binary, code)
├── Detect BOM and encoding markers
└── Report encoding uncertainties
```

#### 1.3 The Record Subsystem

The Record subsystem creates immutable snapshots of observations:

**Snapshot (`observations/record/snapshot.py`)**

```python
@dataclass(frozen=True)
class Snapshot:
    """
    Complete observation snapshot with integrity verification.

    Immutable: Fields cannot be modified after creation.
    Verifiable: Includes SHA256 hash of all observations.
    Dated: Records creation timestamp.
    Provenanced: Links to source paths and parameters.
    """
    snapshot_id: str                           # Unique identifier
    created_at: datetime                       # Creation timestamp
    observations: List[Observation]            # List of observations
    integrity_hash: str                        # SHA256 of all observations
    parameters: Dict[str, Any]                 # Observation parameters
    limitations: List[DeclaredLimitation]      # Known limitations
    evidence_chain: EvidenceChain              # Cryptographic proof
```

**Anchors (`observations/record/anchors.py`)**

Anchors provide stable reference points for observations:

```python
@dataclass(frozen=True)
class Anchor:
    """
    Stable reference point for observations.

    Allows observations to be linked to specific code locations
    that remain valid even as the codebase changes.
    """
    anchor_id: str
    anchor_type: AnchorType                    # FILE, FUNCTION, CLASS, LINE
    path: Path
    reference: str                             # Stable reference (e.g., line number)
    created_in: str                            # Snapshot ID
```

**Integrity (`observations/record/integrity.py`)**

Integrity management for observations:

```python
class IntegrityManager:
    """
    Manages cryptographic integrity for observations.

    Responsibilities:
    ├── Generate SHA256 hashes for observations
    ├── Verify observation integrity
    ├── Maintain evidence chains
    └── Detect tampering
    """

    def hash_observation(self, observation: Observation) -> str:
        """Generate SHA256 hash for an observation."""

    def create_evidence_chain(self, observations: List[Observation]) -> EvidenceChain:
        """Create cryptographic proof chain."""

    def verify_integrity(self, snapshot: Snapshot) -> IntegrityResult:
        """Verify snapshot integrity."""
```

#### 1.4 Limitations Subsystem

Every observation has limitations that must be explicitly declared:

**Declared Limitations (`observations/limitations/declared.py`)**

```python
@dataclass(frozen=True)
class DeclaredLimitation:
    """
    Explicit declaration of observation limitations.

    Every observation must declare what it cannot see.
    This is fundamental to truth preservation.
    """
    limitation_id: str
    category: LimitationCategory              # RUNTIME, SCOPE, TOOL, NATIVE
    description: str                           # Human-readable explanation
    impact: str                                # How this affects conclusions
    workaround: Optional[str]                  # Optional mitigation
```

**Limitation Categories:**

| Category | Description                     | Example                |
| -------- | ------------------------------- | ---------------------- |
| RUNTIME  | Cannot observe runtime behavior | Function return values |
| SCOPE    | Limited by observation scope    | Cross-file patterns    |
| TOOL     | Limited by observation tool     | Binary file parsing    |
| NATIVE   | Inherent limitation             | Encrypted code content |

#### 1.5 Input Validation Subsystem

Input validation ensures observations are safe and bounded:

**Filesystem Validation (`observations/input_validation/filesystem.py`)**

```
Validates:
├── Path traversal prevention
├── Symlink handling rules
├── Permission checking
├── Mount point boundaries
└── Reserved name detection
```

**Binary File Handling (`observations/input_validation/binaries.py`)**

```
Rules:
├── Binary detection before reading
├── Size limits for binary analysis
├── Type-specific handling
└── Quarantine for suspicious files
```

**Size Limits (`observations/input_validation/size_limits.py`)**

```
Boundaries:
├── Maximum files per observation: 10,000
├── Maximum directory depth: 50
├── Maximum file size: 100MB
├── Maximum total size: 1GB
└── Maximum observation time: 30 minutes
```

#### 1.6 Invariants Testing

Invariant tests verify observation layer compliance:

**Immutability Test (`observations/invariants/immutable.test.py`)**

```python
def test_observations_are_immutable():
    """
    Verify observations cannot be modified after creation.

    This is critical for truth preservation.
    """
    observation = create_observation()

    with pytest.raises(FrozenInstanceError):
        observation.modify_field()
```

**No Inference Test (`observations/invariants/no_inference.test.py`)**

```python
def test_no_inference_in_observations():
    """
    Verify observations contain only factual data.

    No interpretation, no inference, no opinion.
    """
    observation = create_file_observation()

    # Only factual fields present
    assert observation.path is not None
    assert observation.size is not None
    assert observation.modified is not None

    # No interpretative fields
    assert not hasattr(observation, 'purpose')
    assert not hasattr(observation, 'quality')
    assert not hasattr(observation, 'bugs')
```

---

### Layer 2: Inquiry (Questions & Patterns)

The Inquiry layer applies human questions and numeric-only pattern analysis to observations. This is where meaning is constructed, but always grounded in observations.

#### 2.1 Core Principles

**Human-Driven Questions**

Users ask questions; the system provides data to help answer them:

```
Question Flow:
1. User formulates question
2. System identifies relevant observations
3. Pattern analysis provides evidence
4. User draws conclusions
```

**Numeric-Only Patterns**

Pattern analysis produces numeric results without interpretation:

| Pattern     | Output                          | Interpretation (NOT included)            |
| ----------- | ------------------------------- | ---------------------------------------- |
| Coupling    | Node degrees (1, 2, 3...)       | "High coupling" (human judgment)         |
| Complexity  | Tree depth (5, 10, 15...)       | "Complex code" (human judgment)          |
| Density     | Import counts (23, 45, 67...)   | "Too many dependencies" (human judgment) |
| Violations  | Boolean (True/False)            | "Bad design" (human judgment)            |
| Uncertainty | Confidence interval (0.85-0.95) | "Probably buggy" (human judgment)        |

#### 2.2 Questions Subsystem

**Structure Questions (`inquiry/questions/structure.py`)**

```python
class StructureQuestions:
    """
    Answers "What exists?" with pure description.

    Constitutional Compliance:
    - Only describes structure, does not evaluate
    - Provides counts and lists, not assessments
    """

    def ask_about_structure(self, snapshot: Snapshot) -> StructureAnswer:
        """
        Describe what exists in the snapshot.

        Returns:
            StructureAnswer with pure descriptions
        """
```

**Connection Questions (`inquiry/questions/connections.py`)**

```python
class ConnectionQuestions:
    """
    Answers "How is it connected?" with dependency data.

    Constitutional Compliance:
    - Shows connections, does not evaluate quality
    - Provides graph data, does not interpret patterns
    """

    def ask_about_connections(self, snapshot: Snapshot) -> ConnectionAnswer:
        """
        Describe module and function connections.
        """
```

**Anomaly Questions (`inquiry/questions/anomalies.py`)**

```python
class AnomalyQuestions:
    """
    Answers "What seems unusual?" with deviation data.

    Constitutional Compliance:
    - Shows statistical deviations, does not judge
    - Provides data points, does not label "bugs"
    """

    def ask_about_anomalies(self, snapshot: Snapshot) -> AnomalyAnswer:
        """
        Identify statistical anomalies.
        """
```

**Purpose Questions (`inquiry/questions/purpose.py`)**

```python
class PurposeQuestions:
    """
    Answers "What does this do?" with signature data.

    Constitutional Compliance:
    - Describes signatures and documentation
    - Does not infer actual behavior
    - Clearly marks assumptions
    """

    def ask_about_purpose(self, snapshot: Snapshot) -> PurposeAnswer:
        """
        Describe declared purpose from signatures.
        """
```

**Thinking Questions (`inquiry/questions/thinking.py`)**

```python
class ThinkingQuestions:
    """
    Answers "What do I think?" - user's own analysis.

    Constitutional Compliance:
    - User's thoughts, not system's
    - Anchored to observations
    - Documented in notebook
    """

    def ask_thinking_question(self, snapshot: Snapshot) -> ThinkingAnswer:
        """
        User's own analysis and conclusions.
        """
```

#### 2.3 Patterns Subsystem

Numeric-only pattern analysis:

**Coupling Patterns (`inquiry/patterns/coupling.py`)**

```python
class CouplingAnalyzer:
    """
    Analyzes coupling patterns without interpretation.

    Output: Node degrees (integers only)
    """

    def analyze_coupling(self, import_observation: ImportObservation) -> List[NodeDegree]:
        """
        Calculate degree metrics for all modules.

        Returns:
            List of (module_name, degree) tuples
            degree = number of imports + number of imports from
        """

    def find_hubs(self, degrees: List[NodeDegree]) -> List[NodeDegree]:
        """
        Find high-degree nodes (hubs).

        Returns:
            Nodes with degree > threshold
        """
```

**Complexity Patterns (`inquiry/patterns/complexity.py`)**

```python
class ComplexityAnalyzer:
    """
    Analyzes complexity patterns without interpretation.

    Output: Numeric metrics only
    """

    def analyze_ast_depth(self, ast_node) -> int:
        """Return AST depth as integer."""

    def analyze_call_depth(self, function_def) -> int:
        """Return maximum call depth as integer."""
```

**Density Patterns (`inquiry/patterns/density.py`)**

```python
class DensityAnalyzer:
    """
    Analyzes density patterns without interpretation.

    Output: Density metrics as floats
    """

    def analyze_import_density(self, module) -> float:
        """Return imports per module as float."""

    def analyze_annotation_density(self, module) -> float:
        """Return type annotation coverage as float."""
```

**Violation Patterns (`inquiry/patterns/violations.py`)**

```python
class ViolationAnalyzer:
    """
    Analyzes boundary violations (boolean only).

    Output: Boolean flags, no interpretation
    """

    def check_boundary_crossing(self, import_stmt) -> bool:
        """Return True if boundary is crossed."""

    def check_circular_dependency(self, module_a, module_b) -> bool:
        """Return True if circular dependency exists."""
```

**Uncertainty Patterns (`inquiry/patterns/uncertainty.py`)**

```python
class UncertaintyAnalyzer:
    """
    Analyzes data completeness and uncertainty.

    Output: Confidence intervals, not conclusions
    """

    def calculate_confidence(self, observation) -> float:
        """Return confidence as float between 0 and 1."""

    def identify_data_gaps(self, observation) -> List[str]:
        """List missing data areas."""
```

#### 2.4 Notebook Subsystem

The notebook is where human thinking is documented:

**Notebook Entry (`inquiry/notebook/entries.py`)**

```python
@dataclass
class NotebookEntry:
    """
    Human thinking anchored to observations.

    Unlike observations, notebook entries CAN be modified.
    They represent human analysis, not objective facts.
    """
    entry_id: str
    snapshot_id: str                          # Link to observations
    anchor_ids: List[str]                     # Evidence anchors
    content: str                              # User's analysis
    created_at: datetime
    tags: List[str]                           # Categorization
    linked_question: Optional[str]            # Original question
```

**Constraints (`inquiry/notebook/constraints.py`)**

Prevents note→observation bleed:

```
Rules:
├── Notebook entries cannot become observations
├── All entries must anchor to observations
├── Evidence must be explicitly cited
├── Interpretations must be labeled
└── Uncertainty must be acknowledged
```

#### 2.5 Session Subsystem

Manages investigation context:

**Session Context (`inquiry/session/context.py`)**

```python
@dataclass(frozen=True)
class SessionContext:
    """
    Immutable investigation session context.
    """
    snapshot_id: str                          # Current snapshot
    anchor_id: str                            # Current focus
    question_type: QuestionType               # Current question category
    context_id: str                           # Unique session ID
```

**Session History (`inquiry/session/history.py`)**

```python
class SessionHistory:
    """
    Linear investigation path tracking.

    Responsibilities:
    ├── Record all questions asked
    ├── Track all observations viewed
    ├── Maintain investigation timeline
    └── Support session recovery
    """
```

---

### Layer 3: Interface (How We Look)

The Interface layer presents information to users through views, navigation, and indicators.

#### 3.1 Views Subsystem

**Overview View (`lens/views/overview.py`)**

```python
class OverviewView(View):
    """
    High-level summary view.

    Shows:
    ├── Investigation status
    ├── Observation counts
    ├── Key metrics
    └── Available actions
    """
```

**Examination View (`lens/views/examination.py`)**

```python
class ExaminationView(View):
    """
    Focused observation examination.

    Shows:
    ├── Selected observation details
    ├── Related evidence
    └── Associated patterns
    """
```

**Patterns View (`lens/views/patterns.py`)**

```python
class PatternsView(View):
    """
    Pattern analysis results.

    Shows:
    ├── Numeric metrics
    ├── Statistical summaries
    └── Comparison data
    """
```

**Connections View (`lens/views/connections.py`)**

```python
class ConnectionsView(View):
    """
    Dependency and connection visualization.

    Shows:
    ├── Module relationships
    ├── Import graphs
    └── Boundary maps
    """
```

**Thinking View (`lens/views/thinking.py`)**

```python
class ThinkingView(View):
    """
    User's notebook and analysis.

    Shows:
    ├── Notebook entries
    ├── Investigation timeline
    └── Personal annotations
    """
```

#### 3.2 Navigation Subsystem

**Workflow (`lens/navigation/workflow.py`)**

```python
class WorkflowStage(Enum):
    """Investigation workflow stages."""
    ORIENTATION = "orientation"                # Getting started
    EXPLORATION = "exploration"                # Broad investigation
    EXAMINATION = "examination"               # Focused analysis
    SYNTHESIS = "synthesis"                   # Drawing conclusions
    COMPLETION = "completion"                 # Wrapping up
```

**Navigation Context (`lens/navigation/context.py`)**

```python
@dataclass(frozen=True)
class NavigationContext:
    """
    Immutable navigation state.
    """
    session_context: SessionContext
    workflow_stage: WorkflowStage
    focus_type: FocusType                      # What we're looking at
    focus_id: str                              # Specific item ID
    current_view: ViewType                    # Current view
```

#### 3.3 Indicators Subsystem

**Error Indicators (`lens/indicators/errors.py`)**

```python
class ErrorIndicator:
    """
    Immutable error state indicator.

    Constitutional Compliance:
    - States facts, not drama
    - Includes uncertainty markers
    - Suggests recovery actions
    """

    def __init__(self, severity: ErrorSeverity, category: ErrorCategory):
        """Create error indicator."""

    @property
    def display_message(self) -> str:
        """Get display message with uncertainty indicator."""
```

**Loading Indicators (`lens/indicators/loading.py`)**

```python
class LoadingIndicator:
    """
    Loading state indicator without progress implications.

    Constitutional Compliance:
    - Does not imply completion
    - Does not estimate time
    - States current state only
    """

    def create_working(context: str, with_timer: bool = False) -> 'LoadingIndicator':
        """Create working indicator."""

    def create_blocked(context: str) -> 'LoadingIndicator':
        """Create blocked indicator."""
```

#### 3.4 Philosophy Subsystem

**Single Focus (`lens/philosophy/single_focus.py`)**

```python
class SingleFocusPolicy:
    """
    Enforces single focus at any time.

    Rules:
    ├── Only one view active
    ├── Only one observation focused
    ├── Only one question driving investigation
    └── Clear transition paths between focuses
    """
```

**Progressive Disclosure (`lens/philosophy/progressive.py`)**

```python
class ProgressiveDisclosurePolicy:
    """
    Manages progressive information disclosure.

    Rules:
    ├── Summary first, detail on demand
    ├── Expandable sections
    ├── Breadcrumb navigation
    └── Clear "show more" paths
    """
```

---

### Layer 4: Bridge (How We Interact)

The Bridge layer handles command execution and external integrations.

#### 4.1 Commands Subsystem

**Investigation Command (`bridge/commands/investigate.py`)**

```python
@dataclass(frozen=True)
class InvestigationRequest:
    """Request for new investigation."""
    type: InvestigationType                    # NEW, RESUME, FORK
    target_path: Path
    scope: InvestigationScope                  # FILE, MODULE, PACKAGE, PROJECT
    parameters: Dict[str, Any]                 # Intent, name, notes


def execute_investigation(
    request: InvestigationRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """
    Execute investigation command.

    Constitutional Compliance:
    - Validates scope before execution
    - Does not assume intent
    - Records all parameters
    - Returns structured results
    """
```

**Observation Command (`bridge/commands/observe.py`)**

```python
@dataclass(frozen=True)
class ObservationRequest:
    """Request for observations."""
    types: Set[ObservationType]                # Which eyes to use
    target_path: Path
    session_id: str
    parameters: Dict[str, Any]                 # Depth, binary, etc.


def execute_observation(
    request: ObservationRequest,
    runtime: Runtime,
    engine: Engine,
    nav_context: NavigationContext,
    session_context: SessionContext
) -> Dict[str, Any]:
    """
    Execute observation command.
    """
```

**Query Command (`bridge/commands/query.py`)**

```python
@dataclass(frozen=True)
class QueryRequest:
    """Request for inquiry."""
    investigation_id: str
    question: str
    question_type: QuestionType
    focus: Optional[str]
    limit: Optional[int]


def execute_query(
    request: QueryRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """
    Execute query command.
    """
```

**Export Command (`bridge/commands/export.py`)**

```python
@dataclass(frozen=True)
class ExportRequest:
    """Request for export."""
    type: ExportType                           # SESSION, OBSERVATION, NOTEBOOK
    format: ExportFormat                       # JSON, MARKDOWN, HTML, PLAIN
    session_id: str
    parameters: Dict[str, Any]                 # Options


def execute_export(
    request: ExportRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """
    Execute export command.
    """
```

#### 4.2 Coordination Subsystem

**Scheduling (`bridge/coordination/scheduling.py`)**

```python
class InvestigationScheduler:
    """
    Manages investigation scheduling and resource allocation.

    Responsibilities:
    ├── Queue management
    ├── Resource limiting
    ├── Priority handling
    └── Timeout enforcement
    """
```

**Caching (`bridge/coordination/caching.py`)**

```python
class ObservationCache:
    """
    Caches observation results for performance.

    Constitutional Compliance:
    - Cache content, not conclusions
    - Cache immutable observations only
    - Invalidate on snapshot change
    └── Never cache inferred data
    """
```

#### 4.3 Integration Subsystem

**Editor Integration (`bridge/integration/editor.py`)**

```python
class EditorIntegration:
    """
    Editor plugin interface.

    Supports:
    ├── VS Code extension
    ├── Vim/Neovim plugin
    ├── Emacs integration
    └── JetBrains plugins
    """
```

**CI/CD Integration (`bridge/integration/ci.py`)**

```python
class CIIntegration:
    """
    CI/CD pipeline integration.

    Supports:
    ├── GitHub Actions
    ├── GitLab CI
    ├── Jenkins pipelines
    └── Azure DevOps
    """
```

**Export Formats (`bridge/integration/export_formats.py`)**

```python
class ExportFormatter:
    """
    Format exports for different consumers.
    """

    def format_json(self, data: Dict) -> str:
        """Format as JSON."""

    def format_markdown(self, data: Dict) -> str:
        """Format as Markdown."""

    def format_html(self, data: Dict) -> str:
        """Format as HTML."""

    def format_plain(self, data: Dict) -> str:
        """Format as plain text."""
```

---

### Layer 5: Core (Execution Spine)

The Core layer is the runtime authority that manages lifecycle, enforcement, and coordination.

#### 5.1 Runtime (`core/runtime.py`)

```python
class Runtime:
    """
    Supreme authority of execution for CodeMarshal.

    Constitutional Guarantees:
    1. No partial execution - either fully initialized or not at all
    2. No degraded mode without explicit explanation
    3. Tier 1 violations cause immediate halt
    4. Deterministic behavior across runs
    5. Complete separation of concerns
    """

    def __init__(self, config: RuntimeConfiguration) -> None:
        """
        Initialize runtime with validation.

        Phase 1: Constitution Validation
        Phase 2: Create Runtime Context
        Phase 3: Initialize Shutdown System
        Phase 4: Activate Runtime Prohibitions
        Phase 5: Verify Constitutional Integrity
        Phase 6: Initialize State Machine
        Phase 7: Create Engine
        """

    def start_investigation(
        self,
        target_path: Path,
        session_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new investigation session.
        """

    def execute(self) -> None:
        """
        Execute full investigation lifecycle.

        Constitutional Guarantee:
        Linear investigation enforced.
        """
```

**Runtime Configuration (`core/context.py`)**

```python
@dataclass(frozen=True)
class RuntimeContext:
    """
    Immutable runtime context.

    Created once during initialization.
    Cannot be modified during execution.
    """
    investigation_root: Path
    constitution_hash: str
    code_version_hash: str
    execution_mode: str                        # CLI, TUI, API, EXPORT
    network_enabled: bool
    mutation_allowed: bool
    runtime_imports_allowed: bool
    session_id: str
    start_timestamp: datetime
```

#### 5.2 Engine (`core/engine.py`)

```python
class Engine:
    """
    Coordinates layers without leaking concerns.

    Responsibilities:
    ├── Layer registration
    ├── Phase execution
    ├── Error coordination
    └── Result aggregation
    """

    def __init__(
        self,
        context: RuntimeContext,
        state: InvestigationState,
        storage: InvestigationStorage,
        memory_monitor: IntegrityMemoryMonitorAdapter
    ):
        """Initialize engine with dependencies."""

    def start_investigation(
        self,
        target_path: Path,
        session_id: Optional[str],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start investigation through layers."""

    def execute_investigation(self) -> None:
        """Execute complete investigation."""
```

#### 5.3 State Machine (`core/state.py`)

```python
class InvestigationPhase(Enum):
    """Investigation phase states."""
    INITIAL = "initial"
    CONSTITUTION_VALIDATED = "constitution_validated"
    ENFORCEMENT_ACTIVE = "enforcement_active"
    OBSERVATION_COLLECTING = "observation_collecting"
    OBSERVATION_COMPLETE = "observation_complete"
    INQUIRY_ACTIVE = "inquiry_active"
    INQUIRY_COMPLETE = "inquiry_complete"
    TERMINATED_NORMAL = "terminated_normal"
    TERMINATED_ERROR = "terminated_error"
    TERMINATED_VIOLATION = "terminated_violation"


class InvestigationState:
    """
    Manages investigation state transitions.

    Guarantees:
    ├── Valid state progression
    ├── Atomic transitions
    ├── Audit trail
    └── Recovery support
    """
```

#### 5.4 Shutdown System (`core/shutdown.py`)

```python
class TerminationReason(Enum):
    """Reasons for termination."""
    NORMAL_COMPLETION = "normal"
    SYSTEM_ERROR = "error"
    CONSTITUTIONAL_VIOLATION = "violation"
    USER_INTERRUPT = "interrupt"


def shutdown(
    reason: TerminationReason,
    exit_code: int,
    error_info: Optional[Tuple[Exception, str]] = None
) -> NoReturn:
    """
    Safe termination with guarantees.

    Guarantees:
    ├── State is persisted
    ├── Resources are released
    ├── Logs are flushed
    └── Proper exit code
    """
```

---

## Constitutional Framework

### Overview

CodeMarshal operates under a constitutional framework that defines non-negotiable rules for behavior, interaction, and architecture.

### The Constitution Document

The constitution is defined in `constitution.truth.md` and contains 24 articles organized into 6 tiers:

#### Tier 1: Foundational Principles (Non-Negotiable)

| Article | Title                  | Description                            |
| ------- | ---------------------- | -------------------------------------- |
| 1       | Observation Purity     | Observations contain only factual data |
| 2       | Human Primacy          | Humans make conclusions, not system    |
| 3       | Truth Preservation     | Evidence chains never break            |
| 4       | Progressive Disclosure | Information revealed progressively     |
| 5       | Interface Purity       | Interface clarifies, never obscures    |
| 6       | Layer Separation       | Strict import boundaries               |

#### Tier 2: Observation Rules

| Article | Title                | Description                       |
| ------- | -------------------- | --------------------------------- |
| 7       | Immutable Facts      | Observations cannot be modified   |
| 8       | Complete Evidence    | All evidence must be recorded     |
| 9       | No Inference         | No interpretation in observations |
| 10      | Declared Limitations | All limits must be stated         |

#### Tier 3: Inquiry Rules

| Article | Title                  | Description                              |
| ------- | ---------------------- | ---------------------------------------- |
| 11      | Question Primacy       | Questions drive analysis                 |
| 12      | Numeric Patterns       | Patterns are numeric, not interpretative |
| 13      | Evidence Anchoring     | All claims must cite evidence            |
| 14      | Uncertainty Expression | Doubt must be expressed                  |

#### Tier 4: Interface Rules

| Article | Title                | Description                    |
| ------- | -------------------- | ------------------------------ |
| 15      | Single Focus         | One thing at a time            |
| 16      | Explicit Transitions | All changes explained          |
| 17      | Recovery Paths       | Escape routes always available |
| 18      | No Hidden State      | All state visible              |

#### Tier 5: Runtime Rules

| Article | Title                  | Description             |
| ------- | ---------------------- | ----------------------- |
| 19      | Local Operation        | No network required     |
| 20      | Deterministic Behavior | Same input, same output |
| 21      | Complete Shutdown      | Graceful termination    |
| 22      | Resource Bounds        | Memory and time limits  |

#### Tier 6: Integration Rules

| Article | Title           | Description                            |
| ------- | --------------- | -------------------------------------- |
| 23      | No Data Leakage | Layers don't leak concerns             |
| 24      | Safe Extensions | Extensions cannot violate constitution |

### Constitutional Validation

```python
from integrity.validation.complete_constitutional import run_constitutional_audit

# Run constitutional audit
validator = run_constitutional_audit()
compliance_score = validator.get_compliance_score()

print(f"Compliance Score: {compliance_score}%")
print(f"Violations: {len(validator.violations)}")
```

### Network Prohibition

```python
from integrity.prohibitions.network_prohibition import run_network_prohibition_tests

# Test network prohibition
network_free = run_network_prohibition_tests()
print(f"Network-free: {network_free}")
```

---

## Data Models & Storage

### Storage Layout

```
storage/
├── investigations/           # Investigation sessions
│   └── {session_id}/
│       ├── session.json      # Session metadata
│       ├── context.json      # Runtime context
│       └── state.json        # State machine state
│
├── snapshots/               # Observation snapshots
│   └── {snapshot_id}/
│       ├── snapshot.json    # Snapshot metadata
│       ├── observations/     # Individual observations
│       │   └── {obs_id}.json
│       └── integrity.json   # Hash chain
│
├── patterns/               # Pattern analysis results
│   └── {snapshot_id}/
│       ├── coupling.json
│       ├── complexity.json
│       ├── density.json
│       └── violations.json
│
├── notebook/               # User's notebook entries
│   └── {session_id}/
│       ├── entries/
│       │   └── {entry_id}.json
│       └── timeline.json
│
└── metadata/               # System metadata
    ├── versions.json
    └── schema_versions.json
```

### Key Data Models

**Session (`storage/schema.py`)**

```python
@dataclass(frozen=True)
class InvestigationSession:
    """
    Investigation session with immutable metadata.
    """
    session_id: str
    created_at: datetime
    target_path: Path
    scope: InvestigationScope
    intent: str
    name: Optional[str]
    initial_notes: Optional[str]
    state: InvestigationPhase
    constitution_hash: str
```

**Snapshot (`storage/schema.py`)**

```python
@dataclass(frozen=True)
class ObservationSnapshot:
    """
    Immutable snapshot of observations.
    """
    snapshot_id: str
    created_at: datetime
    session_id: str
    observations: List[Observation]
    integrity_hash: str
    parameters: Dict[str, Any]
    limitations: List[DeclaredLimitation]
```

**Pattern Results (`storage/schema.py`)**

```python
@dataclass(frozen=True)
class PatternResults:
    """
    Pattern analysis results.
    """
    snapshot_id: str
    coupling: List[NodeDegree]
    complexity: Dict[str, int]
    density: Dict[str, float]
    violations: List[BoundaryViolation]
    uncertainty: Dict[str, float]
```

### Atomic Writing

```python
from storage.atomic import atomic_write

# Write with atomic guarantee
with atomic_write(target_path) as temp_path:
    with open(temp_path, 'w') as f:
        f.write(data)
    # Atomic rename happens here
```

### Corruption Detection

```python
from storage.corruption import CorruptionChecker

class CorruptionChecker:
    """
    Detects storage corruption.

    Checks:
    ├── Hash verification
    ├── Schema compliance
    ├── Reference integrity
    └── Temporal consistency
    """
```

---

## Command Execution Flows

### Investigation Command Flow

```
User: codemarshal investigate /path/to/code --scope=project --intent=initial_scan

1. CLI Parsing (bridge/entry/cli.py)
   ├── Parse arguments
   ├── Validate required parameters
   └── Create InvestigationRequest

2. Runtime Initialization (core/runtime.py)
   ├── Load constitution
   ├── Validate configuration
   ├── Create RuntimeContext
   └── Initialize shutdown system

3. Engine Coordination (core/engine.py)
   ├── Register observation interface
   ├── Register inquiry interface
   └── Create investigation session

4. Observation Collection (observations/eyes/*.py)
   ├── FileSight: Collect file structure
   ├── ImportSight: Collect imports
   ├── ExportSight: Collect definitions
   ├── BoundarySight: Collect boundaries
   └── EncodingSight: Collect encoding info

5. Snapshot Creation (observations/record/snapshot.py)
   ├── Create immutable snapshot
   ├── Generate integrity hash
   ├── Record limitations
   └── Store in storage/

6. Pattern Analysis (inquiry/patterns/*.py)
   ├── Coupling analysis (numeric)
   ├── Complexity analysis (numeric)
   ├── Density analysis (numeric)
   ├── Violation detection (boolean)
   └── Uncertainty calculation (float)

7. Result Return (bridge/results.py)
   ├── Create InvestigationResult
   ├── Return to CLI
   └── Display to user
```

### Observation Command Flow

```
User: codemarshal observe /path/to/code --scope=module

1. CLI Parsing
   ├── Parse arguments
   ├── Create ObservationRequest
   └── Determine observation types

2. Runtime Initialization
   ├── Create minimal runtime
   └── Initialize observation engine

3. Eye Execution
   For each requested eye:
   ├── Validate permissions
   ├── Collect observations
   ├── Apply size limits
   └── Record limitations

4. Result Compilation
   ├── Merge observations
   ├── Calculate integrity hash
   ├── Generate evidence chain
   └── Return structured result
```

### Query Command Flow

```
User: codemarshal query investigation_id --question="What imports exist?" --question-type=connections

1. CLI Parsing
   ├── Parse investigation_id
   ├── Parse question
   └── Determine question type

2. Session Loading
   ├── Load session from storage
   ├── Verify integrity
   └── Load observations

3. Question Processing
   ├── Route to appropriate analyzer
   ├── Identify relevant observations
   ├── Apply pattern analysis
   └── Generate numeric results

4. Result Presentation
   ├── Format answer
   ├── Include evidence citations
   └── Return structured result
```

### Export Command Flow

```
User: codemarshal export investigation_id --format=json --output=report.json

1. CLI Parsing
   ├── Parse investigation_id
   ├── Parse format
   └── Create ExportRequest

2. Data Collection
   ├── Load session data
   ├── Load observations
   ├── Load patterns (if requested)
   └── Load notebook (if requested)

3. Format Conversion
   ├── Apply formatter
   ├── Include metadata
   └── Generate output

4. File Writing
   ├── Atomic write
   ├── Integrity verification
   └── Return success
```

---

## Boundary System

### Overview

The boundary system enforces architectural separation between layers, preventing import dependencies that would violate the architectural design.

### Boundary Rules

```
Allowed Imports:
├── bridge/ CAN import from: lens, inquiry, observations, core, storage, config, integrity
├── lens/ CAN import from: inquiry, observations, core, storage, config
├── inquiry/ CAN import from: observations, core, storage, config
├── observations/ CAN import from: core, storage, config
├── core/ CAN import from: storage, config
├── storage/ CAN import from: config
├── config/ CAN import from: (nothing - root)
└── integrity/ CAN import from: core, storage
```

### Forbidden Imports

```
Forbidden Examples:
├── observations/inquiry (violates Layer 1 ↔ Layer 2)
├── lens/core/engine (violates Layer 3 ↔ Layer 5)
├── bridge/storage/database (violates Bridge ↔ Storage directly)
└── config/core/context (violates Layer 5 ↔ Layer 1)
```

### Boundary Configuration

**Configuration File (`config/boundaries.py`)**

```python
@dataclass(frozen=True)
class BoundaryConfig:
    """
    Boundary configuration for import restrictions.
    """
    layer_name: str
    allowed_imports: Set[str]                  # Module paths allowed
    forbidden_imports: Set[str]                # Explicitly forbidden
    exceptions: Set[str]                       # Approved exceptions


# System boundaries
BOUNDARIES = {
    'core': BoundaryConfig(
        layer_name='core',
        allowed_imports={'storage', 'config'},
        forbidden_imports=set(),
        exceptions=set()
    ),
    'observations': BoundaryConfig(
        layer_name='observations',
        allowed_imports={'core', 'storage', 'config'},
        forbidden_imports={'lens', 'inquiry', 'bridge'},
        exceptions=set()
    ),
    'inquiry': BoundaryConfig(
        layer_name='inquiry',
        allowed_imports={'observations', 'core', 'storage', 'config'},
        forbidden_imports={'lens', 'bridge'},
        exceptions=set()
    ),
    'lens': BoundaryConfig(
        layer_name='lens',
        allowed_imports={'inquiry', 'observations', 'core', 'storage', 'config'},
        forbidden_imports={'bridge'},
        exceptions=set()
    ),
    'bridge': BoundaryConfig(
        layer_name='bridge',
        allowed_imports={'lens', 'inquiry', 'observations', 'core', 'storage', 'config', 'integrity'},
        forbidden_imports=set(),
        exceptions=set()
    ),
}
```

### Boundary Enforcement

```python
from observations.boundary_checker import BoundaryChecker

# Check if import is allowed
checker = BoundaryChecker()
is_allowed = checker.is_import_allowed(
    importing_module='bridge.commands.investigate',
    imported_module='core.runtime'
)
# Returns: True (allowed)

is_allowed = checker.is_import_allowed(
    importing_module='observations.eyes.file_sight',
    imported_module='inquiry.questions.structure'
)
# Returns: False (forbidden - Layer 1 cannot import Layer 2)
```

---

## Security Model

### Threat Model

| Threat                   | Mitigation                        |
| ------------------------ | --------------------------------- |
| Arbitrary code execution | No code execution in observations |
| Path traversal           | Strict path validation            |
| Resource exhaustion      | Size and time limits              |
| Data tampering           | SHA256 integrity hashes           |
| Information disclosure   | Scope-based access control        |
| Denial of service        | Resource bounds enforcement       |

### Network Security

**Article 12: Local Operation**

CodeMarshal is designed to operate without network access:

```python
# Network prohibition test
from integrity.prohibitions.no_network import NoNetworkPolicy

policy = NoNetworkPolicy()
is_compliant = policy.check_network_access()
# True = No network access used
```

### File Security

**Filesystem Safety**

```
Safety Measures:
├── Symlink following requires explicit flag
├── Path traversal blocked by default
├── Mount point boundaries enforced
├── Permission checks before access
├── Reserved name blocking
└── Size limits per file and total
```

### Integrity Verification

```python
from storage.investigation_storage import InvestigationStorage

storage = InvestigationStorage()

# Verify session integrity
result = storage.verify_session(session_id)
print(f"Integrity: {result.integrity_verified}")
print(f"Hashes valid: {result.hashes_valid}")
print(f"References valid: {result.references_valid}")
```

---

## Performance Considerations

### Resource Limits

| Resource               | Limit      | Enforcement         |
| ---------------------- | ---------- | ------------------- |
| Files per observation  | 10,000     | Input validation    |
| Directory depth        | 50         | Traversal control   |
| File size              | 100MB      | Input validation    |
| Total observation size | 1GB        | Size monitoring     |
| Observation time       | 30 minutes | Timeout enforcement |
| Memory usage           | 2GB        | Memory monitoring   |

### Optimization Strategies

**Caching**

```python
from bridge.coordination.caching import ObservationCache

class ObservationCache:
    """
    Caches immutable observations.

    Strategy:
    ├── Cache key = path + parameters
    ├── Invalidation = snapshot change
    ├── Size limit = 100MB cache
    └── LRU eviction
    """
```

**Lazy Loading**

```python
# Observations are loaded on demand
class ObservationManager:
    def get_observation(self, obs_id: str) -> Observation:
        """Load observation from storage when needed."""
```

**Parallel Processing**

```python
from bridge.coordination.scheduling import parallel_execute

# Eyes can run in parallel
results = parallel_execute(
    [file_sight, import_sight, export_sight],
    max_workers=4
)
```

---

## Extension Points

### Adding New Eyes

```python
from observations.eyes.base import AbstractEye, ObservationResult

class CustomSight(AbstractEye):
    """
    Custom observation eye for new data types.
    """

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'type': 'custom_sight',
            'version': '1.0',
            'limitations': ['Cannot observe runtime state']
        }

    def observe(self, path: Path) -> ObservationResult:
        # Implementation
        pass
```

### Adding New Patterns

```python
from inquiry.patterns.base import AbstractPatternAnalyzer

class CustomPatternAnalyzer(AbstractPatternAnalyzer):
    """
    Custom pattern analyzer for new metrics.
    """

    def analyze(self, observation: Observation) -> Dict[str, Any]:
        # Return numeric results only
        return {'metric_name': 42}
```

### Adding New Export Formats

```python
from bridge.integration.export_formats import AbstractExportFormatter

class CustomFormatFormatter(AbstractExportFormatter):
    """
    Custom export formatter.
    """

    def format(self, data: Dict) -> str:
        # Return formatted string
        return custom_format_string
```

### Adding New Integrations

```python
from bridge.integration.editor import AbstractEditorIntegration

class CustomEditorIntegration(AbstractEditorIntegration):
    """
    Custom editor integration.
    """

    def connect(self) -> bool:
        # Establish connection
        pass

    def get_observations(self) -> List[Observation]:
        # Fetch observations
        pass
```

---

## Integration Patterns

### Editor Integration Example (VS Code)

```python
from bridge.integration.editor import EditorIntegration

class CodeMarshalVSCodeExtension:
    """
    VS Code extension for CodeMarshal.
    """

    def __init__(self):
        self.runtime = None

    def activate(self):
        """Called when extension activates."""
        # Create runtime for API mode
        self.runtime = create_runtime(
            investigation_root=Path.cwd(),
            execution_mode="API"
        )

    def investigate_current_file(self):
        """Investigate currently open file."""
        file_path = Path(self.get_active_file_path())
        return self.runtime.start_investigation(file_path)
```

### CI/CD Integration Example (GitHub Actions)

```yaml
name: CodeMarshal Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Constitutional Audit
        run: |
          python -m integrity.validation.complete_constitutional

      - name: Run Network Prohibition Test
        run: |
          python -m integrity.prohibitions.network_prohibition

      - name: Investigate Codebase
        run: |
          codemarshal investigate . \
            --scope=project \
            --intent=architecture_review \
            --name="CI Analysis $(date +%Y-%m-%d)"

      - name: Export Results
        run: |
          codemarshal export latest \
            --format=json \
            --output=investigation.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: investigation-results
          path: investigation.json
```

---

## Troubleshooting Guide

### Common Issues

#### Issue: Import Errors

```
Problem: Cannot import CodeMarshal modules
Solution: Check Python path and virtual environment

import sys
sys.path.insert(0, '/path/to/codemarshal')
```

#### Issue: Storage Errors

```
Problem: Cannot save investigations
Solution: Check permissions and disk space

import os
print(f"Writable: {os.access('/path/to/storage', os.W_OK)}")
```

#### Issue: Constitutional Violations

```
Problem: Constitutional compliance failures
Solution: Run validation and fix reported issues

python -m integrity.validation.complete_constitutional
```

#### Issue: Memory Errors

```
Problem: Out of memory during large investigations
Solution: Reduce scope or increase memory limits

codemarshal observe /path/to/code --scope=module
```

#### Issue: Boundary Violations

```
Problem: Import boundary violation detected
Solution: Check layer dependencies

python -m observations.boundary_checker --verbose
```

### Diagnostic Commands

```bash
# Check system health
codemarshal doctor

# Validate constitution
codemarshal validate constitution

# Check boundaries
codemarshal validate boundaries

# Verify storage integrity
codemarshal validate storage

# View system status
codemarshal status
```

---

## Appendix: File Reference

### Core Layer Files

| File               | Lines | Purpose                                 |
| ------------------ | ----- | --------------------------------------- |
| `core/runtime.py`  | 858   | Runtime authority, lifecycle management |
| `core/engine.py`   | 412   | Layer coordination                      |
| `core/context.py`  | 156   | Runtime context                         |
| `core/state.py`    | 234   | State machine                           |
| `core/shutdown.py` | 89    | Termination                             |

### Observations Layer Files

| File                                  | Purpose                      |
| ------------------------------------- | ---------------------------- |
| `observations/eyes/base.py`           | Abstract eye interface       |
| `observations/eyes/file_sight.py`     | File structure observation   |
| `observations/eyes/import_sight.py`   | Import statement observation |
| `observations/eyes/export_sight.py`   | Definition observation       |
| `observations/eyes/boundary_sight.py` | Boundary observation         |
| `observations/eyes/encoding_sight.py` | Encoding detection           |
| `observations/record/snapshot.py`     | Immutable snapshot           |
| `observations/record/anchors.py`      | Reference points             |
| `observations/record/integrity.py`    | Hash verification            |
| `observations/limitations/*.py`       | Limitation declarations      |

### Inquiry Layer Files

| File                               | Purpose              |
| ---------------------------------- | -------------------- |
| `inquiry/questions/structure.py`   | Structure questions  |
| `inquiry/questions/connections.py` | Connection questions |
| `inquiry/questions/anomalies.py`   | Anomaly questions    |
| `inquiry/questions/purpose.py`     | Purpose questions    |
| `inquiry/questions/thinking.py`    | Thinking questions   |
| `inquiry/patterns/coupling.py`     | Coupling analysis    |
| `inquiry/patterns/complexity.py`   | Complexity analysis  |
| `inquiry/patterns/density.py`      | Density analysis     |
| `inquiry/patterns/violations.py`   | Violation detection  |
| `inquiry/notebook/*.py`            | Notebook management  |

### Lens Layer Files

| File                   | Purpose               |
| ---------------------- | --------------------- |
| `lens/views/*.py`      | View implementations  |
| `lens/navigation/*.py` | Navigation management |
| `lens/indicators/*.py` | Status indicators     |
| `lens/philosophy/*.py` | Interface principles  |

### Bridge Layer Files

| File                       | Purpose                 |
| -------------------------- | ----------------------- |
| `bridge/entry/cli.py`      | CLI implementation      |
| `bridge/commands/*.py`     | Command handlers        |
| `bridge/coordination/*.py` | Scheduling, caching     |
| `bridge/integration/*.py`  | Editor, CI integrations |

### Storage Layer Files

| File                               | Purpose              |
| ---------------------------------- | -------------------- |
| `storage/investigation_storage.py` | Storage interface    |
| `storage/schema.py`                | Data schemas         |
| `storage/atomic.py`                | Atomic writes        |
| `storage/corruption.py`            | Corruption detection |
| `storage/migration.py`             | Schema migrations    |

### Integrity Layer Files

| File                          | Purpose                   |
| ----------------------------- | ------------------------- |
| `integrity/validation/*.py`   | Constitutional validation |
| `integrity/prohibitions/*.py` | Prohibition enforcement   |
| `integrity/monitoring/*.py`   | Runtime monitoring        |
| `integrity/recovery/*.py`     | Backup and restore        |

### Configuration Files

| File                   | Purpose              |
| ---------------------- | -------------------- |
| `config/boundaries.py` | Import boundaries    |
| `config/schema.py`     | Configuration schema |
| `config/loader.py`     | Config loading       |

---

## Document Information

| Property     | Value            |
| ------------ | ---------------- |
| Version      | 1.0.0            |
| Created      | February 5, 2026 |
| Last Updated | February 5, 2026 |
| Authors      | CodeMarshal Team |
| License      | MIT              |

---

_This document is part of the CodeMarshal truth-preserving documentation system. All information is factual and derived from source code analysis._
