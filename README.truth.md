# **🕵️‍♂️ CODEMARSHAL**

**A Truth-Preserving Cognitive Investigation Environment for Code**

---

## **⚖️ THE CODEMARSHAL MANIFESTO**

CodeMarshal is not another static analyzer, not another AI code assistant, and not another dashboard. It is a **cognitive investigation environment** built on one non-negotiable principle: **Truth must be preserved from observation to understanding.**

Most tools try to **think for you**. CodeMarshal helps you **think better** by enforcing epistemic discipline at every layer of investigation.

---

## **🔍 WHAT PROBLEM DOES CODEMARSHAL SOLVE?**

Modern codebases have become epistemically opaque: too large to hold in your head, too interconnected to reason about linearly, too complex to understand without distortion. Traditional approaches fail because they:

| Traditional Tools | CodeMarshal Approach |
|-------------------|----------------------|
| **Hallucinate** with AI guesses | **Witnesses** only what exists in source |
| **Overwhelm** with 1,000 warnings | Shows **one question at a time** |
| **Simplify** with scores (87% quality) | Preserves **full traceability** |
| **Decide** for you (auto-fix) | Helps **you decide** with anchored evidence |
| **Confuse** with jargon | Uses **human questions** not system categories |

CodeMarshal solves this through **epistemic discipline**—a systematic approach that separates what exists from how we understand it from how we look at it.

---

## **🎯 THE THREE LAWS OF CODEMARSHAL**

### **Law 1: Witness, Don't Interpret**
> The system may only record what is textually present in source code. It may never infer, guess, or interpret meaning. Witnessed reality is immutable.

### **Law 2: Support, Don't Replace**
> The system exists to support human curiosity and thinking. It may never make decisions, draw conclusions, or think for humans. Humans ask, pattern, and reflect; the system only assists.

### **Law 3: Clarify, Don't Obscure**
> The interface must make reality clearer, not more confusing. One focus at a time, progressive revelation, clear navigation, honest uncertainty.

These laws are **non-negotiable** and enforced at every level of the system.

---

## **🏗️ ARCHITECTURAL PHILOSOPHY**

```
codemarshal/
├── reality/          # WHAT IS (Layer 1: Immutable observations)
├── understanding/    # HOW WE MAKE SENSE (Layer 2: Questions, patterns, thinking)
├── lens/            # HOW WE LOOK (Layer 3: Interface, navigation, clarity)
├── bridge/          # HOW WE INTERACT (Layer 4: CLI, TUI, API, integration)
└── integrity/       # HOW WE STAY HONEST (Layer 5: Validation, monitoring, recovery)
```

Each layer has **strict boundaries** and **zero leakage**. This separation is what makes truth preservation possible.

---

## **✨ KEY FEATURES**

### **📝 Ground Truth Preservation**
- **Immutable witnessing**: Records only what exists in source code
- **Zero inference**: Never guesses, never assumes, never interprets
- **Deterministic output**: Same code always produces same observations
- **Declared blindness**: Explicitly states what cannot be seen

### **🤔 Human-Centric Investigation**
- **Question-driven workflow**: "What's here? → What does it do? → How is it connected?"
- **Pattern humility**: All patterns marked with uncertainty (🟡 "Review manually")
- **Anchored thinking**: Every note links to specific evidence
- **Session continuity**: Investigations survive crashes and can be resumed

### **👁️ Truth-Preserving Interface**
- **Single attention**: One question, one screen, one focus
- **Progressive disclosure**: Complexity revealed only when requested
- **Clear navigation**: Always know where you are, how you got there
- **Honest performance**: Never freeze silently, always show waiting states

### **🔒 Self-Policing System**
- **Constitutional compliance**: Continuous validation against the Three Laws
- **Truth drift detection**: Alerts when system approaches boundaries
- **Graceful degradation**: Preserves what works when parts fail
- **Immutable audit logs**: Complete history of every investigation

---

## **🚀 GETTING STARTED**

### **Installation**

```bash
# Install from PyPI (coming soon)
pip install codemarshal

# Or install from development source
git clone https://github.com/codemarshal/codemarshal.git
cd codemarshal
pip install -e .
```

### **Quick Start: The 5-Minute Investigation**

```bash
# Launch an interactive investigation
codemarshal investigate /path/to/your/codebase
```

You'll enter the **CodeMarshal Workbench**:

```
🕵️‍♂️ CODEMARSHAL - Investigating: agent-nexus
────────────────────────────────────────────
📂 Case File: What exists here?
  ├─ lobes/ (4 directories, 142 files)
  ├─ common/ (12 directories, 201 files)
  └─ gateway/ (3 directories, 45 files)

────────────────────────────────────────────
[Enter] Inspect  [Q] Questions  [H] Hypotheses  [N] Notes  [B] Back
```

### **Command Line Interface**

```bash
# Collect evidence (witness reality)
codemarshal collect /path/to/codebase --output evidence.json

# Ask specific questions
codemarshal ask evidence.json "What depends on main.py?"
codemarshal ask evidence.json "Show me architectural boundaries"

# Generate investigative hypotheses
codemarshal analyze evidence.json --output hypotheses.json

# Work with your investigative notes
codemarshal notes add --anchor="file@src/main.py:42" --content="Check this coupling"
codemarshal notes search --query="architecture decision"
```

### **Programmatic API**

```python
import codemarshal

# Launch a full investigation
investigation = codemarshal.investigate("/path/to/codebase")

# Or work with individual components
evidence = codemarshal.collect("/path/to/codebase")
hypotheses = codemarshal.analyze(evidence)
notes = codemarshal.Notes(evidence)

# Export your complete investigation
codemarshal.export(investigation, format="markdown")
```

---

## **🔬 THE INVESTIGATION WORKFLOW**

CodeMarshal follows a **natural investigative progression**:

### **Phase 1: Crime Scene Documentation**
```bash
codemarshal collect . --detail=full
```
**Goal:** Record everything that exists without interpretation.

### **Phase 2: Initial Assessment**
```bash
codemarshal investigate .
```
**Navigate through:**
1. **Case File**: What's the overall structure?
2. **Evidence Room**: What does each file contain?
3. **Connection Map**: How are things related?
4. **Hypothesis Board**: What patterns emerge? (🟡 = uncertain)
5. **Detective's Notes**: What do I think?

### **Phase 3: Deep Investigation**
1. **Follow leads**: Click through dependency chains
2. **Test hypotheses**: Examine evidence for each pattern
3. **Record findings**: Anchor notes to specific evidence
4. **Build understanding**: Connect dots across the codebase

### **Phase 4: Case Closure**
```bash
codemarshal export --format=html --include-timeline
```
**Produce:** A complete investigation report with full traceability.

---

## **🎨 INTERFACE GUIDE**

### **The CodeMarshal Workbench (TUI)**

```
🕵️‍♂️ CODEMARSHAL - Case: agent-nexus/backend
────────────────────────────────────────────
📋 CASE FILE
Project: agent-nexus  |  Files: 847  |  Evidence Points: 4,238

📁 lobes/
  ├─ chatbuddy/ (23 files, 142 imports)
  ├─ insightmate/ (19 files, 98 imports)
  ├─ studyflow/ (17 files, 76 imports)
  └─ autoagent/ (21 files, 112 imports)

────────────────────────────────────────────
[→] Select  [Q] Questions  [H] Hypotheses  [N] Notes  [B] Back  [F1] Help
```

**View Types:**
1. **Case File**: Project structure and statistics
2. **Evidence Room**: File contents, imports, exports
3. **Connection Map**: Dependency graphs and relationships
4. **Hypothesis Board**: Detected patterns with uncertainty levels
5. **Detective's Notes**: Your thinking anchored to evidence

**Navigation Principles:**
- **Single focus**: Only one primary content area visible
- **Linear flow**: Natural progression through investigation
- **Clear affordances**: Always show what you can do next
- **Context preservation**: Never lose your place

### **Command Line Interface**

```bash
# EVIDENCE COLLECTION
codemarshal collect .                    # Full evidence collection
codemarshal collect . --target=src/      # Specific directory
codemarshal collect . --compare=main     # Compare with another branch

# INVESTIGATIVE QUESTIONS
codemarshal ask evidence.json "What are the top-level modules?"
codemarshal ask evidence.json "What depends on core/engine.py?"
codemarshal ask evidence.json "Show me circular dependencies"

# HYPOTHESIS GENERATION
codemarshal analyze evidence.json                    # Generate all hypotheses
codemarshal analyze evidence.json --rule=boundaries  # Specific rule set
codemarshal analyze evidence.json --confidence=high  # High-confidence only

# NOTE MANAGEMENT
codemarshal notes add --anchor="import@core.py:15" --note="Check this dependency"
codemarshal notes list --file=core.py
codemarshal notes export --format=markdown

# SYSTEM OPERATIONS
codemarshal validate --constitutional   # Verify system integrity
codemarshal monitor --watch             # Real-time truth preservation monitoring
codemarshal recover --session=latest    # Recover crashed investigation
```

### **Visual Themes**

CodeMarshal uses a **Gotham Detective** aesthetic:
- **Dark theme**: Black/dark gray background
- **Yellow highlights**: Important elements and selections
- **Orange warnings**: Uncertainty indicators (🟡)
- **Clean typography**: Monospaced, highly readable
- **Minimal decoration**: Every pixel serves a purpose

This isn't just styling—it's **cognitive scaffolding** that puts you in the mindset of a detective investigating a complex case.

---

## **🔧 ARCHITECTURE DEEP DIVE**

### **Layer 1: Reality - What Exists**
```
reality/
├── witness/          # Ways of seeing (files, imports, definitions, boundaries)
├── record/           # Immutable storage with stable anchors
├── limitations/      # Honest declarations of blindness
└── integrity/        # Validation of witnessing purity
```
**Promise:** "I will only record what is textually present."

### **Layer 2: Understanding - Making Sense**
```
understanding/
├── questions/        # Human curiosity framework
├── patterns/         # Pattern detection with uncertainty
├── journal/          # Anchored thinking space
└── session/          # Investigation state management
```
**Promise:** "I will help you ask better questions and see patterns without pretending certainty."

### **Layer 3: Lens - How We Look**
```
lens/
├── philosophy/       # Interface design principles
├── viewports/        # Single-focus screens
├── navigation/       # Clear movement through understanding
├── visual/           # Truth-preserving aesthetics
└── performance/      # Responsiveness guarantees
```
**Promise:** "I will make reality clearer, never more confusing."

### **Layer 4: Bridge - Interaction Points**
```
bridge/
├── intents/          # User goals (explore, analyze, document)
├── interfaces/       # CLI, TUI, API access points
└── integration/      # Editor, CI/CD, tool integration
```
**Promise:** "I will meet you where you work."

### **Layer 5: Integrity - Staying Honest**
```
integrity/
├── validation/       # Constitutional compliance checking
├── monitoring/       # Truth drift detection
└── recovery/         # Healing from errors
```
**Promise:** "I will continuously verify that I follow my own rules."

---

## **📚 EXAMPLE INVESTIGATIONS**

### **Case Study 1: Understanding a Legacy Codebase**
```bash
# Day 1: Initial reconnaissance
codemarshal investigate legacy-system/
# Navigate to largest directories
# Use 'H' to see architectural patterns
# Flag unclear areas with notes

# Day 2: Dependency mapping
codemarshal collect legacy-system/ --focus="src/business-logic/"
codemarshal ask evidence.json "What depends on legacy-module.py?"

# Day 3: Risk assessment
codemarshal analyze evidence.json --rule=complexity
codemarshal analyze evidence.json --rule=coupling

# Day 4: Documentation
codemarshal export --format=html --title="Legacy System Investigation"
```

### **Case Study 2: Architectural Review**
```bash
# Collect complete evidence
codemarshal collect . --detail=architectural

# Check boundary integrity
codemarshal analyze evidence.json --rule=boundary_violations

# Examine dependency health
codemarshal analyze evidence.json --rule=circular_dependencies

# Generate review report
codemarshal export --format=markdown \
  --sections="evidence,patterns,notes,recommendations"
```

### **Case Study 3: Pre-Merge Analysis**
```bash
# Witness changes in feature branch
codemarshal collect . --compare=main --output=changes.json

# Ask specific questions about changes
codemarshal ask changes.json "What new dependencies were introduced?"
codemarshal ask changes.json "What existing modules are affected?"

# Quick pattern check
codemarshal analyze changes.json --fast

# Add review notes
codemarshal notes add \
  --anchor="change@new-feature.py:42" \
  --note="Consider splitting this large function" \
  --tag="review" --tag="complexity"
```

---

## **⚙️ CONFIGURATION**

### **Global Configuration**
```yaml
# ~/.config/codemarshal/config.yaml
investigation:
  default_theme: "gotham"
  auto_save: true
  save_interval: 300  # seconds
  max_evidence_size: "1GB"

patterns:
  confidence_levels:
    high: 0.8    # 🟡🟡🟡
    medium: 0.5  # 🟡🟡
    low: 0.2     # 🟡
  enabled_detectors:
    - complexity
    - coupling
    - boundary_violation
    - security

interface:
  tui:
    color_scheme: "dark"
    font_size: 14
    show_progress: true
  cli:
    output_format: "auto"  # auto, json, text
    verbosity: "normal"

export:
  default_format: "markdown"
  include_anchors: true
  include_uncertainty: true
  timeline: true
```

### **Project-Specific Configuration**
```yaml
# .codemarshal.yaml
witness:
  include:
    - "**/*.py"
    - "**/*.ts"
    - "**/*.js"
    - "**/*.md"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
    - "**/.git/**"
    - "**/dist/**"

patterns:
  custom_rules:
    - name: "no_direct_db_access"
      description: "Database access must go through data layer"
      pattern: "import.*(sqlite3|psycopg2|mysql)"
      confidence: "medium"
    - name: "lobe_isolation"
      description: "Lobes must not import from each other"
      pattern: "from lobes\\.(\\w+) import.*lobes\\.(?!\\1)\\w+"
      confidence: "high"

journal:
  auto_tag:
    - "architecture"
    - "bug"
    - "performance"
    - "security"
  templates:
    decision: "DECISION: {summary}\n\nRATIONALE: {rationale}\n\nEVIDENCE: {evidence}"
    question: "QUESTION: {question}\n\nCONTEXT: {context}"

integration:
  editors:
    vscode: true
    neovim: true
    sublime: false
  ci_cd:
    github_actions: true
    gitlab_ci: true
    jenkins: false
```

---

## **🔬 ADVANCED USAGE**

### **Custom Pattern Detectors**
```python
# detectors/architectural_rules.py
from codemarshal.patterns import BaseDetector, Hypothesis, Confidence

class LobeIsolationDetector(BaseDetector):
    """Detects violations of lobe isolation principle."""
    
    def detect(self, evidence):
        hypotheses = []
        for import_ in evidence.filter(type="import"):
            if self._is_cross_lobe_import(import_):
                hypotheses.append(Hypothesis(
                    title="Potential lobe isolation violation",
                    description=f"Import from {import_.source} to {import_.target}",
                    confidence=Confidence.MEDIUM,
                    evidence_anchors=[import_.anchor],
                    rule="lobe_isolation",
                    recommendation="Review architecture boundaries"
                ))
        return hypotheses
```

### **Plugin Development**
```python
# plugins/security_audit.py
from codemarshal.plugins import BasePlugin

class SecurityAuditPlugin(BasePlugin):
    name = "security_audit"
    version = "1.0.0"
    
    def enhance_evidence(self, evidence):
        """Add security-specific evidence collection."""
        # Your custom evidence collection
        pass
    
    def generate_hypotheses(self, evidence):
        """Generate security-specific hypotheses."""
        # Your custom hypothesis generation
        pass
    
    def enhance_interface(self, interface):
        """Add security-specific views to interface."""
        # Your custom interface enhancements
        pass
```

### **Batch Investigation Automation**
```python
# scripts/batch_investigate.py
import codemarshal
from pathlib import Path

def investigate_projects(projects_dir):
    results = []
    
    for project_path in Path(projects_dir).iterdir():
        if project_path.is_dir():
            print(f"Investigating: {project_path.name}")
            
            # Collect evidence
            evidence = codemarshal.collect(project_path)
            
            # Generate hypotheses
            hypotheses = codemarshal.analyze(evidence)
            
            # Export findings
            report = codemarshal.export(
                evidence=evidence,
                hypotheses=hypotheses,
                format="json"
            )
            
            results.append({
                "project": project_path.name,
                "evidence_points": len(evidence),
                "hypotheses": len(hypotheses),
                "high_confidence_issues": len([h for h in hypotheses if h.confidence == "high"]),
                "report": report
            })
    
    return results
```

### **Continuous Monitoring**
```bash
# Set up continuous truth monitoring
codemarshal monitor --watch --project=/path/to/project

# This provides:
# - Real-time evidence collection on file changes
# - Hypothesis regeneration when code changes
# - Alerting when confidence levels change
# - Automated reporting on investigation drift
```

---

## **🔗 INTEGRATION ECOSYSTEM**

### **Editor Integration**
- **VS Code**: Real-time investigation sidebar
- **Neovim**: Terminal integration with key bindings
- **Sublime Text**: Plugin for quick evidence collection
- **IntelliJ**: Full IDE integration

### **CI/CD Pipeline**
```yaml
# .github/workflows/codemarshal.yml
name: CodeMarshal Investigation
on: [push, pull_request]

jobs:
  investigate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install CodeMarshal
        run: pip install codemarshal
      - name: Collect evidence
        run: codemarshal collect . --output evidence.json
      - name: Analyze for critical issues
        run: |
          codemarshal analyze evidence.json \
            --confidence=high \
            --output hypotheses.json
      - name: Generate investigation report
        run: codemarshal export --format=markdown --output investigation.md
      - name: Upload investigation report
        uses: actions/upload-artifact@v3
        with:
          name: codemarshal-report
          path: investigation.md
```

### **Export Formats**
- **Markdown**: Human-readable investigation reports
- **HTML**: Interactive investigation browsers
- **JSON**: Machine-readable full evidence
- **PDF**: Printable case files
- **Jupyter Notebooks**: Interactive investigation notebooks

---

## **📊 BENCHMARKS & PERFORMANCE**

CodeMarshal is designed for **truth at scale**:

| Metric | Small Project (1k files) | Medium Project (10k files) | Large Project (100k files) |
|--------|--------------------------|----------------------------|----------------------------|
| Evidence collection | 2-5 seconds | 30-60 seconds | 5-10 minutes |
| Hypothesis generation | 1-2 seconds | 10-20 seconds | 2-5 minutes |
| Memory usage | 50-100 MB | 200-500 MB | 1-2 GB |
| TUI responsiveness | <50ms | <100ms | <200ms |

**Optimization strategies:**
- **Incremental evidence collection**: Only process changed files
- **Smart caching**: Cache evidence and hypothesis results
- **Lazy loading**: Load detailed evidence only when needed
- **Parallel processing**: Multi-core evidence collection

---

## **🧩 EXTENDING CODEMARSHAL**

### **Adding New Evidence Collectors**
```python
from codemarshal.reality import BaseWitness

class CustomWitness(BaseWitness):
    name = "custom_evidence"
    limitations = ["Cannot witness runtime behavior"]
    
    def witness(self, file_path):
        # Your custom witnessing logic
        evidence = self._extract_custom_evidence(file_path)
        return self._create_evidence(evidence, anchor=file_path)
```

### **Creating Custom Hypothesis Generators**
```python
from codemarshal.understanding import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    rule_name = "my_custom_rule"
    confidence_calibration = 0.7
    
    def analyze(self, evidence):
        hypotheses = []
        # Your custom analysis logic
        for item in evidence.filter(type="my_custom_type"):
            if self._matches_pattern(item):
                hypotheses.append(self._create_hypothesis(
                    evidence=[item],
                    confidence=self._calculate_confidence(item)
                ))
        return hypotheses
```

### **Building Custom Interfaces**
```python
from codemarshal.lens import BaseView

class CustomView(BaseView):
    name = "my_custom_view"
    description = "A custom view for specialized investigation"
    
    def render(self, investigation):
        # Your custom rendering logic
        return self._render_custom_interface(investigation)
```

---

## **🔒 SECURITY & PRIVACY**

### **Security Principles**
- **Local-first**: All analysis happens on your machine
- **No telemetry**: No data leaves your machine without explicit consent
- **Code review**: Entire codebase is open for security review
- **Minimal dependencies**: Carefully curated dependency tree

### **Privacy Guarantees**
- **Your code stays yours**: Never uploaded to cloud services
- **Your thoughts stay private**: Notes and investigations stored locally
- **Zero tracking**: No usage analytics, no tracking, no surveillance
- **Export control**: You decide what to share and with whom

### **Security Features**
- **Evidence integrity verification**: SHA-256 hashing of all evidence
- **Secure note storage**: Optional encryption for sensitive investigations
- **Audit trails**: Complete history of all investigative actions
- **Access control**: Project-level investigation permissions

---

## **🤝 CONTRIBUTING**

CodeMarshal is built on **epistemic discipline**—this extends to how we build it.

### **Contribution Principles**
1. **Truth over convenience**: Never compromise truth preservation for features
2. **Discipline over speed**: Follow the architecture, even when slower
3. **Clarity over cleverness**: Write code that's obvious, not clever
4. **Validation over trust**: All contributions must pass constitutional checks

### **Development Workflow**
```bash
# 1. Fork and clone
git clone https://github.com/codemarshal/codemarshal.git

# 2. Install development dependencies
pip install -e ".[dev]"

# 3. Run constitutional validation
python -m codemarshal.integrity.validate --constitutional

# 4. Make changes (following architecture layers)

# 5. Run all validation tests
pytest tests/ --constitutional

# 6. Submit pull request with:
#    - Epistemic impact statement
#    - Constitutional compliance report
#    - Layer boundary validation
```

### **Constitutional Compliance**
All contributions must pass:
- **Layer boundary tests**: No mixing of reality/understanding/lens
- **Truth preservation tests**: No inference, no guessing
- **Interface clarity tests**: Single focus, progressive disclosure
- **Performance tests**: Responsiveness maintained

---

## **📜 LICENSE & CITATION**

CodeMarshal is released under the **Truth Preservation License**—a modified MIT license that requires preservation of epistemic discipline in derivative works.

### **Academic Citation**
```bibtex
@software{codemarshal2024,
  title = {CodeMarshal: A Truth-Preserving Cognitive Investigation Environment},
  author = {CodeMarshal Contributors},
  year = {2024},
  url = {https://github.com/codemarshal/codemarshal},
  note = {Epistemic discipline for code understanding}
}
```

### **Commercial Use**
For commercial use, please review the license terms. The core principle: **Truth preservation cannot be compromised, even in commercial derivatives.**

---

## **🚨 TROUBLESHOOTING**

### **Common Issues & Solutions**

**Issue**: "Evidence collection is slow"
**Solution**: Use incremental collection: `codemarshal collect . --incremental`

**Issue**: "Too many hypotheses to review"
**Solution**: Filter by confidence: `codemarshal analyze . --confidence=high`

**Issue**: "TUI feels unresponsive"
**Solution**: Reduce detail level: `codemarshal investigate . --detail=medium`

**Issue**: "Can't understand the output"
**Solution**: Use the guided interface: `codemarshal investigate . --guided`

**Issue**: "System claims constitutional violation"
**Solution**: Run diagnostics: `codemarshal validate --diagnose`

### **Getting Help**
- **Documentation**: `codemarshal --help` or `F1` in TUI
- **Community**: GitHub Discussions for epistemic discussions
- **Issues**: GitHub Issues for bug reports and feature requests
- **Guided investigation**: `codemarshal investigate . --tutorial`

---

## **🌟 WHY "CODEMARSHAL"?**

A **marshal** is an officer who preserves order, maintains boundaries, and ensures proper procedure. A **CodeMarshal** does the same for understanding code:

1. **Preserves truth** through immutable evidence
2. **Maintains boundaries** between layers of understanding  
3. **Ensures procedure** through constitutional compliance
4. **Guides investigation** without taking over

We're not building another tool. We're building **the first environment where truth about code can be preserved, investigated, and understood without distortion.**

---

## **🚀 READY TO INVESTIGATE?**

```bash
# Start your first investigation
pip install codemarshal
codemarshal investigate /path/to/your/mysterious/codebase

# Join the truth preservation movement
# https://github.com/codemarshal/codemarshal
# https://codemarshal.dev
```

**Remember:** In a world of AI hallucinations and overwhelming complexity, sometimes what we need isn't more intelligence—it's more discipline. CodeMarshal provides that discipline.

**Happy investigating, Marshal.** 🕵️‍♂️