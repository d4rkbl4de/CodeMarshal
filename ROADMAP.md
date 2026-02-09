# CodeMarshal v2.1 - Development Roadmap

**Version:** 2.1.0  
**Codename:** Renaissance  
**Timeline:** 20 weeks (5 months)  
**Last Updated:** February 8, 2026

---

## Executive Summary

CodeMarshal v2.1 transforms the investigation tool into a production-ready, multi-language, IDE-integrated platform with 47 built-in patterns, 5 programming languages, 3 IDE integrations, and a desktop GUI.

---

## Phase 0: Foundation Repair (Week 0)

### Critical Bug Fixes

- **Fix Type Annotation Error** (`observations/record/integrity.py:308`)
  - Change `callable` to `Callable` from typing
  - Impact: Unblocks entire import chain

- **Verify Import Chain**
  - Test all module imports
  - Fix circular dependencies

---

## Phase 1: Pattern System Renaissance (Weeks 1-3)

### 1.1 Pattern Libraries

**Performance Patterns (20 patterns)**

```yaml
# patterns/builtin/performance.yaml
patterns:
  - id: nested_loop_n2
    name: "O(n²) Nested Loop"
    pattern: "for\s+.*:\s*\n\s+for\s+.*:\s*\n\s+for\s+"
    severity: warning
    description: "Triple nested loop detected"

  - id: large_function
    name: "Large Function (>50 lines)"
    pattern: "def\s+\w+\s*\([^)]*\):\s*(?:[^}]*\n){50,}"
    severity: info

  - id: sync_io_loop
    name: "Synchronous I/O in Loop"
    pattern: "for\s+.*:\s*\n\s+(open|read|write|request|fetch)\("
    severity: warning
    suggestion: "Consider async/await or batching"

  - id: n_plus_one
    name: "N+1 Query Pattern"
    pattern: "for\s+.*:\s*\n\s+.*\.(get|filter|query|find)\("
    severity: warning
    suggestion: "Use select_related/prefetch"
```

**Style Patterns (15 patterns)**

```yaml
# patterns/builtin/style.yaml
patterns:
  - id: missing_docstring
    name: "Missing Docstring"
    pattern: "^def\s+(?!__).*:\s*(?!\s*[\"'])"
    severity: info

  - id: bare_except
    name: "Bare Except Clause"
    pattern: "except\s*:"
    severity: warning

  - id: mutable_default
    name: "Mutable Default Argument"
    pattern: "def\s+\w+\s*\([^)]*=\s*(\[\s*\}|\{\s*\})"
    severity: critical
```

**Architecture Patterns (12 patterns)**

```yaml
# patterns/builtin/architecture.yaml
patterns:
  - id: cross_layer_import
    name: "Cross-Layer Import Violation"
    pattern: "from\s+(inquiry|lens)\s+import.*core"
    severity: critical

  - id: god_class
    name: "God Class (>30 methods)"
    pattern: "class\s+\w+.*:\s*(?:.*def\s+\w+.*\n){30,}"
    severity: warning
```

### 1.2 Pattern Engine Enhancements

```python
# patterns/engine.py
class PatternEngine:
    """Advanced pattern detection with context awareness."""

    def detect_with_context(self, file_path: Path, pattern: PatternDefinition) -> list[PatternMatch]:
        """Detect patterns with surrounding code context."""
        # Implementation

    def detect_statistical_outliers(self, codebase: Path) -> list[StatisticalAnomaly]:
        """Find statistically unusual patterns using z-score analysis."""
        # Implementation

    def suggest_fix(self, match: PatternMatch) -> FixSuggestion | None:
        """Suggest automated fixes."""
        # Implementation
```

### 1.3 Pattern Dashboard

```python
# lens/views/pattern_dashboard.py
class PatternDashboardView:
    """Interactive pattern results with Rich terminal UI."""

    def render(self, matches: list[PatternMatch]):
        # Summary statistics
        # Severity distribution chart
        # File heatmap
        # Match details with context
```

### Deliverables

- [ ] 47 built-in patterns (20 performance + 15 style + 12 architecture)
- [ ] Pattern engine with context awareness
- [ ] Statistical outlier detection
- [ ] Automated fix suggestions
- [ ] Interactive dashboard

---

## Phase 2: Inquiry System Deepening (Weeks 4-5)

### 2.1 Enhanced Analyzers

**Structure Analyzer**

```python
def analyze(self, observations: list[dict], question: str) -> str:
    question_lower = question.lower()

    if "metrics" in question_lower:
        return self._analyze_metrics(observations)
    elif "graph" in question_lower:
        return self._generate_structure_graph(observations)
    elif "complexity" in question_lower:
        return self._analyze_complexity_distribution(observations)
```

**Connection Mapper**

```python
def analyze(self, observations: list[dict], question: str) -> str:
    if "circular" in question_lower:
        return self._detect_circular_dependencies(observations)
    elif "impact" in question_lower:
        return self._analyze_impact_surface(observations, question)
    elif "centrality" in question_lower:
        return self._calculate_centrality(observations)
```

**Anomaly Detector**

```python
def analyze(self, observations: list[dict], question: str) -> str:
    if "statistical" in question_lower:
        return self._detect_statistical_outliers(observations)
    elif "architecture" in question_lower:
        return self._detect_architecture_anomalies(observations)
```

### Deliverables

- [ ] 4+ analysis modes per analyzer
- [ ] Circular dependency detection (DFS algorithm)
- [ ] Impact surface analysis
- [ ] Module centrality calculation
- [ ] Statistical outlier detection

---

## Phase 3: Multi-Language Support (Weeks 6-8)

### 3.1 Language Detection

```python
# observations/eyes/language_detector.py
class LanguageDetector:
    LANGUAGE_SIGNATURES = {
        "python": {
            "extensions": [".py", ".pyw"],
            "markers": ["def ", "import ", "class ", "__init__"],
            "weight": 0.6
        },
        "javascript": {
            "extensions": [".js", ".jsx"],
            "markers": ["function", "const ", "=>", "require("],
            "weight": 0.6
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "markers": ["interface ", "type ", ": string"],
            "weight": 0.6
        },
        "java": {
            "extensions": [".java"],
            "markers": ["public class", "import java."],
            "weight": 0.6
        },
        "go": {
            "extensions": [".go"],
            "markers": ["package ", "func ", ":="],
            "weight": 0.6
        }
    }
```

### 3.2 Language-Specific Observers

**JavaScript/TypeScript**

```python
# observations/eyes/javascript_sight.py
class JavaScriptSight(AbstractEye):
    def observe_imports(self, path: Path) -> JSImportObservation:
        # ES6 imports, CommonJS requires, dynamic imports

    def observe_exports(self, path: Path) -> JSExportObservation:
        # ES6 exports, CommonJS exports
```

**Java**

```python
# observations/eyes/java_sight.py
class JavaSight(AbstractEye):
    def observe_imports(self, path: Path) -> JavaImportObservation:
        # Package imports, static imports

    def observe_classes(self, path: Path) -> JavaClassObservation:
        # Class, interface, enum definitions
```

**Go**

```python
# observations/eyes/go_sight.py
class GoSight(AbstractEye):
    def observe_imports(self, path: Path) -> GoImportObservation:
        # Import blocks, aliased imports

    def observe_packages(self, path: Path) -> GoPackageObservation:
        # Package declaration, module detection
```

### Deliverables

- [ ] Language detector (95%+ accuracy)
- [ ] JavaScript/TypeScript sight
- [ ] Java sight
- [ ] Go sight
- [ ] Unified multi-language API

---

## Phase 4: IDE Integration Suite (Weeks 9-10)

### 4.1 VS Code Extension

```typescript
// vscode-extension/src/extension.ts
export function activate(context: vscode.ExtensionContext) {
  // Commands
  vscode.commands.registerCommand("codemarshal.investigate", investigateFile);
  vscode.commands.registerCommand("codemarshal.showPatterns", showPatterns);

  // CodeLens for functions/classes
  vscode.languages.registerCodeLensProvider(
    languages,
    new CodeMarshalCodeLensProvider(),
  );

  // Hover information
  vscode.languages.registerHoverProvider(
    languages,
    new CodeMarshalHoverProvider(),
  );

  // Diagnostics on save
  vscode.workspace.onDidSaveTextDocument(checkPatterns);
}
```

### 4.2 Neovim Plugin

```lua
-- nvim-plugin/lua/codemarshal/init.lua
local M = {}

function M.setup(opts)
    -- Commands
    vim.api.nvim_create_user_command('CodeMarshalInvestigate', investigate)
    vim.api.nvim_create_user_command('CodeMarshalPatterns', show_patterns)

    -- Keymaps
    vim.keymap.set('n', '<leader>ci', ':CodeMarshalInvestigate<CR>')
    vim.keymap.set('n', '<leader>cp', ':CodeMarshalPatterns<CR>')

    -- Diagnostics
    if opts.lint_on_save then
        vim.api.nvim_create_autocmd('BufWritePost', {
            pattern = {'*.py', '*.js', '*.ts'},
            callback = check_patterns
        })
    end
end

return M
```

### 4.3 JetBrains Plugin

```kotlin
// jetbrains-plugin/src/main/kotlin/CodeMarshalService.kt
@Service
class CodeMarshalService(private val project: Project) {
    fun investigateFile(virtualFile: VirtualFile) {
        // Run codemarshal CLI
    }

    fun showPatternHighlights(editor: Editor) {
        // Add range highlighters for patterns
    }
}
```

### Deliverables

- [ ] VS Code extension (6 commands, CodeLens, hover, diagnostics)
- [ ] Neovim Lua plugin (commands, keymaps, floating windows)
- [ ] JetBrains plugin foundation (highlights, tool window)

---

## Phase 5: Desktop GUI (Weeks 11-12)

### 5.1 PySide6 Application Shell

```python
# desktop/app.py
from PySide6 import QtWidgets

def main():
    # Initialize application
    # Load theme and icon resources
    # Launch primary window
    pass
```

### 5.2 Core Screens (Single-Focus)

```python
# desktop/views/home.py
class HomeView(QtWidgets.QWidget):
    # Title: "CodeMarshal"
    # Subtitle: "made by d4rkblblade"
    # Primary action: Select codebase
    pass
```

```python
# desktop/views/observe.py
class ObserveView(QtWidgets.QWidget):
    # Run observe command
    # Show summary + violations
    pass
```

```python
# desktop/views/investigate.py
class InvestigateView(QtWidgets.QWidget):
    # Guided question/answer flow
    pass
```

```python
# desktop/views/patterns.py
class PatternsView(QtWidgets.QWidget):
    # Filterable list + severity badges
    pass
```

```python
# desktop/views/export.py
class ExportView(QtWidgets.QWidget):
    # Export formats + file path
    pass
```

### 5.3 Theme, Typography, Icons

```python
# desktop/theme.py
PALETTE = {
    "background": "#0B0B0C",
    "surface_primary": "#151518",
    "surface_secondary": "#1D1E22",
    "accent": "#E0C469",
    "text_primary": "#F0F0F0",
    "text_secondary": "#A0A0A0",
}
```

### Deliverables

- [ ] PySide6 desktop GUI (Windows/Linux/macOS)
- [ ] Mandatory GUI entrypoint (`codemarshal gui`)
- [ ] Single-focus screens (Home, Observe, Investigate, Patterns, Export)
- [ ] Dark, high-contrast theme with detective typography
- [ ] Local-only operation (no network dependencies)

---

## Phase 6: Storage & Data Layer (Weeks 13-14)

### 6.1 Migration System

```python
# storage/migration.py
class MigrationManager:
    CURRENT_SCHEMA_VERSION = "2.1.0"

    def migrate(self, target_version: str = None):
        # Run migrations sequentially
        # Support rollback

    def _migrate_2_0_to_2_1(self):
        # Add pattern_matches table
        # Add file_languages table
        # Migrate existing data
```

### 6.2 Transactional Storage

```python
# storage/transactional.py
class TransactionalStorage:
    @contextmanager
    def transaction(self):
        # BEGIN TRANSACTION
        # Yield
        # COMMIT or ROLLBACK

    def save_investigation(self, investigation: Investigation) -> str:
        # Atomic save with all related data
```

### 6.3 Knowledge Base

```python
# knowledge/base.py
class KnowledgeBase:
    def add_insight(self, investigation_id: str, insight: Insight):
        # Store insight

    def search_insights(self, query: str) -> list[Insight]:
        # Full-text search

    def get_pattern_trends(self, pattern_id: str) -> Trend:
        # Historical pattern data

    def find_similar_codebases(self, investigation_id: str) -> list[Similarity]:
        # Pattern-based similarity
```

### Deliverables

- [ ] Migration system with versioning
- [ ] ACID transaction support
- [ ] Knowledge base with insights
- [ ] Pattern trends over time
- [ ] Similar codebase detection

---

## Phase 7: Test Suite Completion (Weeks 15-16)

### 7.1 End-to-End Tests

```python
# tests/end_to_end/test_full_workflow.py
class TestFullWorkflow:
    def test_investigate_query_export_workflow(self, tmp_path):
        # Create test codebase
        # Run investigation
        # Query results
        # Export and verify

    def test_multi_language_investigation(self, tmp_path):
        # Create mixed codebase
        # Verify all languages detected
```

### 7.2 Performance Tests

```python
# tests/performance/test_large_codebase.py
class TestLargeCodebasePerformance:
    @pytest.mark.slow
    def test_1000_files_investigation(self, tmp_path):
        # Should complete in <60 seconds

    @pytest.mark.slow
    def test_10000_files_investigation(self, tmp_path):
        # Should complete in <5 minutes
```

### 7.3 Constitutional Compliance Tests

```python
# tests/invariants/test_constitutional_compliance.py
class TestConstitutionalCompliance:
    def test_article_1_observation_purity(self):
        # No inference keywords in observations

    def test_article_9_layer_independence(self):
        # Check import boundaries

    def test_article_12_local_operation(self):
        # No network libraries used
```

### Deliverables

- [ ] 20+ end-to-end tests
- [ ] Performance benchmarks (1k, 10k, 100k files)
- [ ] Constitutional compliance tests
- [ ] 90%+ code coverage

---

## Phase 8: Advanced Export & Visualization (Weeks 17-18)

### 8.1 Jupyter Export

```python
# bridge/integration/jupyter_exporter.py
class JupyterExporter(BaseExporter):
    def export(self, investigation: Investigation) -> str:
        # Generate .ipynb with:
        # - Markdown cells for summary
        # - Code cells with investigation data
        # - Interactive visualizations
```

### 8.2 PDF Report

```python
# bridge/integration/pdf_exporter.py
class PDFExporter(BaseExporter):
    def export(self, investigation: Investigation) -> bytes:
        # Professional formatting with:
        # - Executive summary
        # - Pattern tables
        # - Architecture diagrams
```

### 8.3 SVG Architecture Diagrams

```python
# bridge/integration/svg_exporter.py
class SVGExporter(BaseExporter):
    def export(self, investigation: Investigation) -> str:
        # Generate SVG with:
        # - Color-coded nodes by layer
        # - Dependency edges
        # - Interactive tooltips
```

### Deliverables

- [ ] Jupyter notebook export
- [ ] PDF report generation
- [ ] SVG architecture diagrams
- [ ] Interactive HTML export

---

## Phase 9: Plugin System (Weeks 19-20)

### 9.1 Plugin Architecture

```python
# plugins/base.py
class CodeMarshalPlugin:
    """Base class for all plugins."""

    name: str
    version: str

    def activate(self, api: PluginAPI):
        pass

    def enhance_observations(self, observations: list) -> list:
        return observations

    def analyze_patterns(self, observations: list) -> list:
        return []
```

### 9.2 Sample Plugins

```python
# plugins/example_django/analyzer.py
class DjangoPlugin(CodeMarshalPlugin):
    """Django-specific analysis."""

    def activate(self, api: PluginAPI):
        api.register_pattern(PatternDefinition(
            id="django_n_plus_one",
            pattern=r"for\s+.*:\s*\n\s+.*\.(get|filter)\(",
            severity="warning"
        ))
```

### Deliverables

- [ ] Plugin base class and API
- [ ] Plugin loader with discovery
- [ ] 3+ sample plugins
- [ ] Plugin documentation

---

## Timeline Summary

| Phase   | Duration | Weeks | Deliverables                   |
| ------- | -------- | ----- | ------------------------------ |
| Phase 0 | 3 days   | 0     | Bug fixes                      |
| Phase 1 | 3 weeks  | 1-3   | 47 patterns, engine, dashboard |
| Phase 2 | 2 weeks  | 4-5   | Enhanced analyzers             |
| Phase 3 | 3 weeks  | 6-8   | 5 languages                    |
| Phase 4 | 2 weeks  | 9-10  | 3 IDE integrations             |
| Phase 5 | 2 weeks  | 11-12 | Desktop GUI                    |
| Phase 6 | 2 weeks  | 13-14 | Storage, knowledge base        |
| Phase 7 | 2 weeks  | 15-16 | Test suite                     |
| Phase 8 | 2 weeks  | 17-18 | Advanced exports               |
| Phase 9 | 2 weeks  | 19-20 | Plugin system                  |

**Total:** 20 weeks (5 months)

---

## Success Metrics

- **Patterns:** 8 → 47 (+39)
- **Languages:** 1 → 5 (+4)
- **IDEs:** 0 → 3 (+3)
- **Test Coverage:** 70% → 90%+ (+20%)
- **Lines of Code:** 87k → 127k (+40k)

---

## New Files Created

```
patterns/
  ├── engine.py
  ├── builtin/performance.yaml
  ├── builtin/style.yaml
  └── builtin/architecture.yaml

observations/eyes/
  ├── language_detector.py
  ├── javascript_sight.py
  ├── java_sight.py
  └── go_sight.py

desktop/
  ├── app.py
  ├── theme.py
  ├── resources.qrc
  ├── icons/
  └── views/
      ├── home.py
      ├── observe.py
      ├── investigate.py
      ├── patterns.py
      └── export.py

plugins/
  ├── base.py
  ├── loader.py
  └── example_django/

knowledge/
  └── base.py

vscode-extension/
nvim-plugin/
jetbrains-plugin/
```

---

## Implementation Order

1. Start with Phase 0 (critical bug fix)
2. Phase 1-3 can overlap (patterns, inquiry, languages)
3. Phase 4-5 (IDE, desktop GUI) can run in parallel
4. Phase 6-9 should be sequential

---

## Notes

- All code must follow constitutional principles
- Maintain 24 constitutional articles
- No external network dependencies
- Truth preservation is paramount
- Every feature must include tests
- Document all public APIs
