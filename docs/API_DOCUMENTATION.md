# **CODEMARSHAL API DOCUMENTATION**

**Version:** 0.1.0  
**Last Updated:** January 16, 2026  

---

## **OVERVIEW**

CodeMarshal provides a truth-preserving cognitive investigation environment for understanding complex codebases. This API documentation covers the core interfaces for programmatic access.

**Core Philosophy:** Truth preservation through observation, inquiry, and interface layers without inference or interpretation.

---

## **ARCHITECTURAL LAYERS**

### **Layer 1: Core System**
```python
from core.runtime import Runtime
from core.engine import Engine
from core.context import RuntimeContext
```

### **Layer 2: Observations**
```python
from observations.eyes.file_sight import FileSight
from observations.eyes.import_sight import ImportSight
from observations.record.snapshot import Snapshot
```

### **Layer 3: Inquiry**
```python
from inquiry.questions.structure import StructureQuestions
from inquiry.patterns.coupling import CouplingAnalyzer
from inquiry.session.context import SessionContext
```

### **Layer 4: Interface**
```python
from lens.views.overview import OverviewView
from lens.indicators.errors import ErrorIndicator
from lens.indicators.loading import LoadingIndicator
```

### **Layer 5: Bridge**
```python
from bridge.commands.investigate import execute_investigation
from bridge.commands.export import execute_export
from bridge.entry.cli import CLI
```

---

## **CORE API**

### **Runtime Management**

#### **Runtime Class**
```python
class Runtime:
    """Main runtime coordinator for CodeMarshal operations."""
    
    def __init__(self, storage: InvestigationStorage = None):
        """Initialize runtime with optional storage backend."""
    
    def start_investigation(self, path: Path) -> SessionContext:
        """Start a new investigation on the given path."""
    
    def stop_investigation(self, session_id: str) -> bool:
        """Stop the current investigation and save state."""
    
    def get_current_session(self) -> Optional[SessionContext]:
        """Get the currently active investigation session."""
```

#### **Usage Example**
```python
from core.runtime import Runtime
from storage.investigation_storage import InvestigationStorage

# Initialize runtime
storage = InvestigationStorage()
runtime = Runtime(storage=storage)

# Start investigation
session = runtime.start_investigation(Path("/path/to/codebase"))
print(f"Investigation started: {session.snapshot_id}")

# Stop investigation
success = runtime.stop_investigation(session.snapshot_id)
print(f"Investigation saved: {success}")
```

---

## **OBSERVATION API**

### **File Observation**

#### **FileSight Class**
```python
class FileSight(AbstractEye):
    """Observes filesystem structure without interpretation."""
    
    def observe(self, path: Path, depth: int = -1) -> FileObservation:
        """Observe files and directories at given path."""
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get observation capabilities and limitations."""
```

#### **Usage Example**
```python
from observations.eyes.file_sight import FileSight

# Create observer
file_sight = FileSight()

# Observe directory
observation = file_sight.observe(Path("/path/to/project"), depth=3)

print(f"Found {len(observation.files)} files")
print(f"Capabilities: {file_sight.get_capabilities()}")
```

### **Import Observation**

#### **ImportSight Class**
```python
class ImportSight(AbstractEye):
    """Observes static import statements without execution."""
    
    def observe(self, path: Path) -> ImportObservation:
        """Observe imports in Python files at given path."""
    
    def analyze_dependencies(self, observation: ImportObservation) -> DependencyGraph:
        """Analyze dependency relationships from observations."""
```

#### **Usage Example**
```python
from observations.eyes.import_sight import ImportSight

# Create import observer
import_sight = ImportSight()

# Observe imports
observation = import_sight.observe(Path("/path/to/project"))

print(f"Found {len(observation.statements)} import statements")
print(f"Modules imported: {observation.module_imports}")

# Analyze dependencies
deps = import_sight.analyze_dependencies(observation)
print(f"Dependency graph: {deps}")
```

---

## **INQUIRY API**

### **Structure Questions**

#### **StructureQuestions Class**
```python
class StructureQuestions:
    """Answers "What exists?" with pure description."""
    
    def ask_about_structure(self, snapshot: Snapshot) -> StructureAnswer:
        """Describe what exists in the snapshot."""
    
    def get_file_counts(self, snapshot: Snapshot) -> Dict[str, int]:
        """Get counts by file type."""
```

#### **Usage Example**
```python
from inquiry.questions.structure import StructureQuestions
from observations.record.snapshot import Snapshot

# Create structure analyzer
questions = StructureQuestions()

# Analyze structure
answer = questions.ask_about_structure(snapshot)

print(f"Directories: {answer.directory_count}")
print(f"Python files: {answer.python_file_count}")
```

### **Pattern Analysis**

#### **CouplingAnalyzer Class**
```python
class CouplingAnalyzer:
    """Analyzes coupling patterns without interpretation."""
    
    def analyze_coupling(self, import_observation: ImportObservation) -> List[NodeDegree]:
        """Calculate degree metrics for all modules."""
    
    def find_hubs(self, degrees: List[NodeDegree]) -> List[NodeDegree]:
        """Find high-degree nodes (hubs)."""
```

#### **Usage Example**
```python
from inquiry.patterns.coupling import CouplingAnalyzer
from observations.eyes.import_sight import ImportSight

# Create analyzer
analyzer = CouplingAnalyzer()

# Get import observation
import_sight = ImportSight()
import_obs = import_sight.observe(Path("/path/to/project"))

# Analyze coupling
degrees = analyzer.analyze_coupling(import_obs)
hubs = analyzer.find_hubs(degrees)

print(f"Analyzed {len(degrees)} modules")
print(f"Found {len(hubs)} hub modules")
```

---

## **INTERFACE API**

### **Error Indicators**

#### **ErrorIndicator Class**
```python
class ErrorIndicator:
    """Immutable error state indicator without drama."""
    
    def __init__(self, severity: ErrorSeverity, category: ErrorCategory):
        """Create error indicator with severity and category."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export error state for logging."""
    
    @property
    def display_message(self) -> str:
        """Get display message with uncertainty indicator."""
```

#### **Usage Example**
```python
from lens.indicators.errors import ErrorIndicator, ErrorSeverity, ErrorCategory

# Create error indicator
error = ErrorIndicator(
    severity=ErrorSeverity.RECOVERABLE,
    category=ErrorCategory.OBSERVATION_FAILED
)

print(f"Error: {error.display_message}")
print(f"Can continue: {error.can_continue_operations}")
```

### **Loading Indicators**

#### **LoadingIndicator Class**
```python
class LoadingIndicator:
    """Loading state indicator without progress implications."""
    
    def create_working(context: str, with_timer: bool = False) -> 'LoadingIndicator':
        """Create working indicator."""
    
    def create_blocked(context: str) -> 'LoadingIndicator':
        """Create blocked indicator."""
```

#### **Usage Example**
```python
from lens.indicators.loading import LoadingIndicator

# Create loading indicator
loading = LoadingIndicator.create_working(
    context="Analyzing dependencies",
    with_timer=True
)

print(f"State: {loading.state.description}")
print(f"Elapsed: {loading.elapsed_seconds}s")
```

---

## **BRIDGE API**

### **Command Execution**

#### **Investigation Command**
```python
def execute_investigation(
    request: InvestigationRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """Execute investigation command with constitutional compliance."""
```

#### **Export Command**
```python
def execute_export(
    request: ExportRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """Execute export command with truth preservation."""
```

#### **Usage Example**
```python
from bridge.commands.investigate import execute_investigation, InvestigationRequest
from bridge.commands.export import execute_export, ExportRequest

# Create investigation request
investigate_request = InvestigationRequest(
    path=Path("/path/to/project"),
    scope="project",
    intent="initial_scan"
)

# Execute investigation
result = execute_investigation(
    request=investigate_request,
    runtime=runtime,
    session_context=session_context,
    nav_context=nav_context
)

# Create export request
export_request = ExportRequest(
    type=ExportType.SESSION,
    format=ExportFormat.JSON,
    session_id=session_context.snapshot_id,
    output_path=Path("/path/to/export.json")
)

# Execute export
export_result = execute_export(
    request=export_request,
    runtime=runtime,
    session_context=session_context,
    nav_context=nav_context
)
```

---

## **STORAGE API**

### **Investigation Storage**

#### **InvestigationStorage Class**
```python
class InvestigationStorage:
    """Persistent storage for investigations with integrity."""
    
    def save_session(self, session: SessionContext) -> bool:
        """Save session with atomic write and integrity check."""
    
    def load_session(self, session_id: str) -> Optional[SessionContext]:
        """Load session with integrity verification."""
    
    def create_backup(self, session_id: str) -> Path:
        """Create backup of session."""
```

#### **Usage Example**
```python
from storage.investigation_storage import InvestigationStorage
from inquiry.session.context import SessionContext

# Create storage
storage = InvestigationStorage(base_path=Path("/path/to/storage"))

# Save session
session = SessionContext(snapshot_id="test-001", ...)
success = storage.save_session(session)

# Load session
loaded_session = storage.load_session("test-001")

# Create backup
backup_path = storage.create_backup("test-001")
```

---

## **CONSTITUTIONAL COMPLIANCE**

### **Self-Validation**
```python
from integrity.validation.complete_constitutional import run_constitutional_audit

# Run constitutional audit
validator = run_constitutional_audit()
compliance_score = validator.get_compliance_score()

print(f"Compliance Score: {compliance_score}%")
print(f"Violations: {len(validator.violations)}")
```

### **Network Prohibition**
```python
from integrity.prohibitions.network_prohibition import run_network_prohibition_tests

# Test network prohibition
network_free = run_network_prohibition_tests()

print(f"Network-free: {network_free}")
```

---

## **ERROR HANDLING**

### **Error Types**
```python
# Constitutional violations
class ConstitutionalViolation(Exception):
    """Raised when constitutional rules are violated."""

# Runtime errors
class CoordinationError(Exception):
    """Raised during engine coordination problems."""

# Storage errors
class IntegrityError(Exception):
    """Raised when data integrity is compromised."""
```

### **Best Practices**
```python
try:
    # CodeMarshal operation
    result = execute_investigation(request, runtime, session_context, nav_context)
except ConstitutionalViolation as e:
    # Handle constitutional violation
    print(f"Constitutional violation: {e}")
except CoordinationError as e:
    # Handle coordination error
    print(f"Coordination failed: {e}")
except Exception as e:
    # Handle unexpected error
    print(f"Unexpected error: {e}")
```

---

## **INTEGRATION EXAMPLES**

### **Editor Integration**
```python
# VS Code extension example
from codemarshal import Runtime, InvestigationStorage

class CodeMarshalExtension:
    def __init__(self):
        self.runtime = Runtime()
        self.storage = InvestigationStorage()
    
    def investigate_current_file(self):
        """Investigate currently open file."""
        file_path = Path(self.get_active_file())
        session = self.runtime.start_investigation(file_path)
        return session
```

### **CI/CD Integration**
```python
# GitHub Actions example
- name: Constitutional Analysis
  run: |
    python -m integrity.validation.complete_constitutional
    python -m integrity.prohibitions.network_prohibition
    
- name: Investigation
  run: |
    codemarshal investigate . --scope=project --intent=initial_scan
    
- name: Export Results
  run: |
    codemarshal export latest --format=json --output=investigation.json
```

---

## **CONFIGURATION**

### **Environment Variables**
```bash
# CodeMarshal configuration
CODEMARSHAL_STORAGE_PATH=/path/to/storage
CODEMARSHAL_LOG_LEVEL=INFO
CODEMARSHAL_CONSTITUTIONAL_MODE=strict
```

### **Configuration File**
```yaml
# .codemarshal.yaml
investigation:
  default_depth: 5
  max_file_size: 10MB
  
storage:
  base_path: ~/.codemarshal
  backup_enabled: true
  
constitutional:
  enforcement_mode: strict
  auto_validate: true
```

---

## **LIMITATIONS**

### **Observation Limitations**
- Cannot observe runtime behavior
- Cannot execute code during observation
- Cannot access network resources
- Limited by filesystem permissions

### **Inquiry Limitations**
- Cannot infer intent or purpose
- Cannot make autonomous decisions
- Limited by observation quality
- Cannot access external knowledge

### **Interface Limitations**
- Single focus enforced
- No real-time updates
- Limited by terminal capabilities
- No multimedia content

---

## **TROUBLESHOOTING**

### **Common Issues**

#### **Import Errors**
```python
# Problem: Cannot import CodeMarshal modules
# Solution: Check Python path and virtual environment
import sys
sys.path.insert(0, '/path/to/codemarshal')
```

#### **Storage Errors**
```python
# Problem: Cannot save investigations
# Solution: Check permissions and disk space
import os
print(f"Writable: {os.access('/path/to/storage', os.W_OK)}")
```

#### **Constitutional Violations**
```python
# Problem: Constitutional compliance failures
# Solution: Run validation and fix reported issues
python -m integrity.validation.complete_constitutional
```

---

## **VERSION COMPATIBILITY**

### **Python Requirements**
- Python 3.11+
- No external dependencies for core functionality
- Optional dependencies for specific features

### **Backward Compatibility**
- All APIs maintain backward compatibility
- Old investigations remain readable
- Migration path provided for breaking changes

---

## **SUPPORT**

### **Documentation**
- API Documentation: This file
- Constitutional Guide: `CONSTITUTIONAL_AUDIT_REPORT.md`
- Architecture Guide: `Structure.md`

### **Issues**
- Report bugs: GitHub Issues
- Feature requests: GitHub Discussions
- Constitutional questions: GitHub Discussions

### **Community**
- Contributing Guide: `CONTRIBUTING.md`
- Code of Conduct: `CODE_OF_CONDUCT.md`
- License: `LICENSE`

---

**API Documentation Version: 0.1.0**  
**Last Updated: January 16, 2026**  
**Next Update: As needed based on user feedback**
