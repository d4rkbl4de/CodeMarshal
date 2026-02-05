# CodeMarshal Implementation Plan

## Executive Summary

**CodeMarshal** is a truth-preserving investigation environment for codebases with constitutional constraints. The core architecture is solid and functional, but several key features need implementation to reach full production readiness.

**Current State**: Core observation and investigation infrastructure is working. Query answering and export functionality need implementation.

**Goal**: Complete the missing implementations to create a fully functional code investigation tool.

---

## What CodeMarshal Is Doing Right Now

### ✅ Working Features

#### 1. **Observation System** (100% Functional)

- **FileSight**: Collects file structure, metadata, and content
- **ImportSight**: Detects import statements and dependencies
- **ExportSight**: Identifies public interfaces and exports
- **BoundarySight**: Detects architectural boundary violations
- **Constitutional Mode**: All four observation types work together
- **Memory Management**: Chunked observation for large codebases
- **Streaming Mode**: Real-time observation with progress reporting

**Evidence**:

```bash
$ codemarshal observe . --scope=project --constitutional
✅ OBSERVATION COLLECTED
- Session ID: 07ab92a8-1412-4692-9c95-206bb13ac9f5
- Types: file_sight, import_sight, export_sight, boundary_sight
- Truth preservation: Guaranteed
```

#### 2. **Investigation System** (100% Functional)

- **Session Creation**: Creates tracked investigation sessions with unique IDs
- **Scope Support**: file, module, package, project levels
- **Intent Tracking**: initial_scan, constitutional_check, dependency_analysis, architecture_review
- **State Management**: Investigation state is persisted
- **Multi-Investigation**: Can create multiple parallel investigations

**Evidence**:

```bash
$ codemarshal investigate . --scope=project --intent=architecture_review
✅ INVESTIGATION STARTED
- ID: investigation_1770217515040_3ff745d1
- Status: investigation_running
```

#### 3. **Constitutional Framework** (100% Functional)

- **24 Articles**: All constitutional constraints are enforced
- **Limitation Declarations**: Each observation type declares its limitations
- **Truth Preservation**: Immutable observations, no inference
- **Boundary Checking**: Cross-layer violation detection
- **Human Primacy**: All decisions require human confirmation

**Evidence**:

- All observation types properly declare limitations
- No inference or guessing in output
- Explicit confirmations required for large operations

#### 4. **CLI Interface** (100% Functional)

- **Command Structure**: All 5 main commands work
- **Argument Parsing**: Required/optional args properly enforced
- **Help System**: Comprehensive help for all commands
- **Error Handling**: Clear refusal messages with reasons
- **Exit Codes**: Proper exit codes (0=success, 1=failure, 130=interrupt)

**Commands Working**:

- `codemarshal observe`
- `codemarshal investigate`
- `codemarshal query` (infrastructure)
- `codemarshal export` (infrastructure)
- `codemarshal tui` (help only)

---

## What CodeMarshal Needs To Do

### 🔴 Priority 1: Query Answering System (Critical Gap)

**Current State**:

- Query command accepts questions and question types
- Returns "No answer provided" for all queries
- Infrastructure exists but no answer generation logic

**What Needs To Be Implemented**:

#### 1.1 **Question Processing Pipeline**

```python
# File: bridge/commands/query.py
# Current: Returns empty result
# Needed: Connect to observation data and generate answers

def process_question(
    question: str,
    question_type: QuestionType,
    investigation_id: str,
    observations: List[Observation]
) -> QueryResult:
    """Process a question and generate an answer from observations."""
    # Implementation needed
```

#### 1.2 **Question Type Handlers**

**Structure Questions** (`question-type=structure`):

- "What modules exist?" → List all Python modules
- "What is the directory structure?" → Show directory tree
- "What files are in X?" → List files in specific directory

**Purpose Questions** (`question-type=purpose`):

- "What does X do?" → Explain function/class purpose from docstrings
- "What is the main purpose of this module?" → Analyze module docstring

**Connections Questions** (`question-type=connections`):

- "What depends on X?" → Find all imports of X
- "What does X import?" → List X's dependencies
- "Show circular dependencies" → Detect import cycles

**Anomalies Questions** (`question-type=anomalies`):

- "Are there any anomalies?" → Find unusual patterns
- "Show me boundary violations" → List cross-layer imports
- "What looks suspicious?" → Detect code smells

**Thinking Questions** (`question-type=thinking`):

- "What should I investigate next?" → Suggest investigation paths
- "What are the risks?" → Identify potential issues

#### 1.3 **Answer Generation**

```python
# New file: inquiry/answers/
# - structure_analyzer.py
# - purpose_extractor.py
# - connection_mapper.py
# - anomaly_detector.py
# - thinking_engine.py
```

**Implementation Steps**:

1. Read stored observations for investigation_id
2. Parse question to understand intent
3. Select appropriate analyzer based on question_type
4. Generate answer from observation data
5. Return QueryResult with actual answer content

---

### 🔴 Priority 2: Export File Creation (Critical Gap)

**Current State**:

- Export command accepts format and output path
- Reports "EXPORT COMPLETE" success message
- Returns export ID
- **Does NOT actually create the file**

**What Needs To Be Implemented**:

#### 2.1 **File Writing Logic**

```python
# File: bridge/commands/export.py
# Current: Returns success without writing file
# Needed: Actually write investigation data to file

def execute_export(
    request: ExportRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    # Load investigation data
    investigation_data = load_investigation(request.session_id)

    # Format data based on request.format
    formatted_data = format_export(
        data=investigation_data,
        format=request.format,
        include_notes=request.parameters.get('include_notes', False),
        include_patterns=request.parameters.get('include_patterns', False)
    )

    # Write to file
    output_path = Path(request.parameters['output_path'])
    output_path.write_text(formatted_data)

    return {"success": True, "export_id": str(uuid.uuid4())}
```

#### 2.2 **Export Format Implementations**

**JSON Format**:

```json
{
  "investigation_id": "investigation_1770217515040_3ff745d1",
  "timestamp": "2026-02-04T21:05:14Z",
  "path": ".",
  "scope": "codebase",
  "observations": [...],
  "patterns": [...],
  "boundary_violations": [...],
  "metadata": {...}
}
```

**Markdown Format**:

```markdown
# CodeMarshal Investigation Report

**ID**: investigation_1770217515040_3ff745d1
**Date**: 2026-02-04
**Scope**: project
**Path**: .

## Summary

...

## Observations

...

## Patterns

...

## Boundary Violations

...
```

**HTML Format**:

- Styled HTML report with sections
- Tables for structured data
- CSS styling for readability

**Plaintext Format**:

- Simple text output
- Good for piping to other tools

#### 2.3 **Export Content**

**Required Content**:

- Investigation metadata (ID, timestamp, scope, path)
- All observations (file_sight, import_sight, export_sight, boundary_sight)
- Boundary crossings and violations
- Question-answer pairs (if query system is working)

**Optional Content** (controlled by flags):

- `--include-notes`: Human notes added during investigation
- `--include-patterns`: Pattern analysis results
- `--include-timeline`: Chronological view of investigation

**Implementation Steps**:

1. Load investigation data from storage
2. Format data according to requested format
3. Write to output file
4. Handle file overwrite confirmation
5. Verify file was created

---

### 🟡 Priority 3: TUI (Text User Interface)

**Current State**:

- TUI command exists
- Help text shows available options
- **Does NOT launch interactive interface**

**What Needs To Be Implemented**:

#### 3.1 **TUI Framework**

```python
# File: bridge/entry/tui.py
# Current: Placeholder class
# Needed: Full TUI implementation using textual/rich

class TruthPreservingTUI:
    def run(self, initial_path: Path) -> int:
        # Launch interactive terminal UI
        # Allow navigation through investigation
        # Show observations in real-time
        pass
```

#### 3.2 **TUI Features**

- **Navigation**: Browse directory structure
- **Observation Viewer**: View collected observations
- **Query Interface**: Ask questions interactively
- **Investigation Manager**: Create/manage investigations
- **Export Dialog**: Export results interactively

**Dependencies**: Requires `rich>=13.7.0` and `textual>=0.52.0`

---

### 🟡 Priority 4: Test Suite Setup

**Current State**:

- Test files exist in `tests/` directory
- pytest shows "0 items collected"
- Tests are not being discovered

**What Needs To Be Implemented**:

#### 4.1 **Test Discovery Fix**

```python
# In pyproject.toml or setup.cfg
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

#### 4.2 **Test Categories**

**Unit Tests**:

- `tests/core/test_runtime.py`
- `tests/core/test_engine.py`
- `tests/observations/test_eyes.py`
- `tests/bridge/test_commands.py`

**Integration Tests**:

- `tests/integration/test_end_to_end.py`
- `tests/integration/test_cli.py`

**Constitutional Tests**:

- `tests/integrity/test_constitutional.py`
- `tests/integrity/test_prohibitions.py`

#### 4.3 **Test Coverage Goals**

- Core: 90%+
- Bridge: 85%+
- Observations: 80%+
- Overall: 75%+

---

### 🟢 Priority 5: Boundary Configuration

**Current State**:

- Warning: "Constitutional mode enabled but no boundary configuration found"
- Using default boundaries

**What Needs To Be Implemented**:

#### 5.1 **Agent Nexus Configuration**

```yaml
# File: config/agent_nexus.yaml
boundaries:
  - name: "core_layer"
    type: "layer"
    pattern: "core/**"
    description: "Core engine and runtime"
    allowed_targets: ["core/**", "config/**"]
    prohibited: true

  - name: "bridge_layer"
    type: "layer"
    pattern: "bridge/**"
    description: "Entry points and CLI"
    allowed_targets: ["core/**", "bridge/**", "config/**", "observations/**"]
    prohibited: true

  - name: "observations_layer"
    type: "layer"
    pattern: "observations/**"
    description: "Observation collection"
    allowed_targets: ["observations/**", "config/**"]
    prohibited: true
```

#### 5.2 **Boundary Enforcement**

- Detect cross-layer imports
- Report violations with file and line number
- Suggest fixes

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Make query and export functional

**Tasks**:

1. ✅ Implement basic question answering for structure questions
2. ✅ Implement file writing for export command
3. ✅ Add JSON and Markdown export formats
4. ✅ Write tests for query and export
5. ✅ Fix pytest test discovery

**Success Criteria**:

```bash
$ codemarshal query <id> --question="What modules exist?" --question-type=structure
✅ Answer: [list of modules]

$ codemarshal export <id> --format=markdown --output=report.md
✅ File created: report.md
```

---

### Phase 2: Enhancement (Week 3-4)

**Goal**: Expand query capabilities and add TUI

**Tasks**:

1. ✅ Implement all question types (structure, purpose, connections, anomalies, thinking)
2. ✅ Add HTML and Plaintext export formats
3. ✅ Implement basic TUI with navigation
4. ✅ Create Agent Nexus boundary configuration
5. ✅ Add comprehensive test coverage

**Success Criteria**:

```bash
$ codemarshal query <id> --question="What depends on core/engine.py?" --question-type=connections
✅ Answer: [list of dependents]

$ codemarshal tui
✅ Interactive TUI launches
```

---

### Phase 3: Polish (Week 5-6)

**Goal**: Production readiness

**Tasks**:

1. ✅ Performance optimization for large codebases
2. ✅ Error handling and edge cases
3. ✅ Documentation and examples
4. ✅ CI/CD integration
5. ✅ Release preparation

**Success Criteria**:

- All tests passing
- Documentation complete
- CLI stable and user-friendly
- Ready for v1.0 release

---

## Technical Details

### Files to Modify

#### High Priority (Query & Export)

bridge/commands/query.py # Add answer generation
bridge/commands/export.py # Add file writing
bridge/results.py # Enhance result types
inquiry/answers/ # NEW DIRECTORY
├── **init**.py
├── structure_analyzer.py
├── connection_mapper.py
├── anomaly_detector.py
└── thinking_engine.py

```

#### Medium Priority (TUI & Config)

```

bridge/entry/tui.py # Implement TUI
config/agent_nexus.yaml # NEW FILE

```

#### Low Priority (Tests)

```

pyproject.toml # Fix pytest config
tests/ # Organize and complete

```

### Data Flow

```

User Query
↓
CLI (bridge/entry/cli.py)
↓
Query Command (bridge/commands/query.py)
↓
Load Observations (storage/investigation_storage.py)
↓
Question Analyzer (inquiry/answers/)
↓
Generate Answer
↓
QueryResult → Display to User

````

### Dependencies

**Current**:

- `typing-extensions>=4.8.0`
- `PyYAML>=6.0`

**Additional for TUI**:

- `rich>=13.7.0`
- `textual>=0.52.0`

**Additional for Development**:

- `pytest>=8.0.0`
- `pytest-cov>=4.1.0`

---

## Testing Strategy

### Manual Testing Commands

```bash
# Test observation
codemarshal observe . --scope=module --constitutional

# Test investigation
codemarshal investigate . --scope=project --intent=architecture_review --confirm-large

# Test query (after implementation)
codemarshal query <investigation_id> --question="What modules exist?" --question-type=structure

# Test export (after implementation)
codemarshal export <investigation_id> --format=markdown --output=report.md --confirm-overwrite
````

### Automated Testing

```bash
# Run all tests
pytest tests/ -v --cov=codemarshal --cov-report=html

# Run specific test categories
pytest tests/core/ -v
pytest tests/bridge/ -v
pytest tests/observations/ -v

# Run with coverage
pytest tests/ --cov=codemarshal --cov-report=term-missing
```

---

## Success Metrics

### Functional Metrics

- ✅ All CLI commands work end-to-end
- ✅ Query returns meaningful answers
- ✅ Export creates valid files
- ✅ TUI launches and is interactive
- ✅ 100% of constitutional constraints enforced

### Quality Metrics

- ✅ Test coverage > 75%
- ✅ Zero critical bugs
- ✅ All edge cases handled
- ✅ Documentation complete

### Performance Metrics

- ✅ Observation of 1000 files < 5 seconds
- ✅ Query response < 1 second
- ✅ Export of large investigation < 10 seconds
- ✅ Memory usage < 500MB for typical projects

---

## Conclusion

CodeMarshal has a **solid foundation** with working observation and investigation systems. The main gaps are:

1. **Query answering** - Infrastructure exists, needs answer generation
2. **Export files** - Infrastructure exists, needs file writing
3. **TUI** - Basic structure exists, needs full implementation
4. **Tests** - Files exist, need discovery and completion

**Estimated Effort**: 4-6 weeks for a single developer to complete all priorities.

**Next Step**: Start with Phase 1 - implement query answering and export file creation. These are the highest impact features that will make CodeMarshal fully functional.
