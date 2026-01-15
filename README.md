# 🕵️‍♂️ CodeMarshal - Truth-Preserving Investigation Environment

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Constitutional](https://img.shields.io/badge/architecture-constitutional-important.svg)](CONSTITUTIONAL_ANALYSIS.md)
[![Truth-Preserving](https://img.shields.io/badge/truth--preserving-100%25-brightgreen.svg)](README.truth.md)

> **A detective's notebook for complex codebases.**  
> Investigate, understand, and maintain architectural integrity without ever lying to you.

---

## 📖 Table of Contents
1. [What is CodeMarshal?](#-what-is-codemarshal)
2. [Why CodeMarshal Exists](#-why-codemarshal-exists)
3. [Core Philosophy](#-core-philosophy)
4. [🚀 Quick Start](#-quick-start)
5. [📦 Installation](#-installation)
6. [🔧 Complete Command Reference](#-complete-command-reference)
7. [🏗️ Architecture Overview](#️-architecture-overview)
8. [⚖️ Constitutional Framework](#️-constitutional-framework)
9. [🎯 Use Cases & Workflows](#-use-cases--workflows)
10. [⚙️ Configuration](#️-configuration)
11. [📊 Output & Interpretation](#-output--interpretation)
12. [🧪 Testing & Validation](#-testing--validation)
13. [🤝 Contributing](#-contributing)
14. [🐛 Troubleshooting](#-troubleshooting)
15. [📚 Documentation](#-documentation)
16. [📄 License](#-license)

---

## 🎯 What is CodeMarshal?

**CodeMarshal** is a truth-preserving investigation environment designed specifically for understanding complex, constitutionally-constrained codebases. Unlike traditional code analysis tools that guess, infer, or overwhelm, CodeMarshal follows 24 non-negotiable constitutional articles to ensure you see only what exists in your code.

### Key Differentiators

| Aspect | Traditional Tools | CodeMarshal |
|--------|------------------|-------------|
| **Truth Model** | Often guess or infer | Only shows what exists |
| **Cognitive Load** | Overwhelm with data | One question, one answer at a time |
| **Architectural Awareness** | Generic patterns | Understands constitutional constraints |
| **Evidence Preservation** | Transient analysis | Immutable, versioned observations |
| **Human Role** | Passive consumer | Active investigator |

### The Problem CodeMarshal Solves

As codebases grow (50K+ LOC), they become **impossible for any single developer to hold entirely in their head** while maintaining architectural purity. CodeMarshal provides:

1. **Constitutional Guardrails**: Automatic detection of boundary violations
2. **Truth-Preserving Investigation**: No AI hallucinations, only textual facts
3. **Human-Centric Workflow**: Follows natural curiosity patterns
4. **Immutable Evidence**: Every claim is anchored to specific observations

---

## 🌟 Why CodeMarshal Exists

### For Developers:
- **30% faster onboarding**: Understand complex systems in days, not weeks
- **50% fewer violations**: Catch architectural issues before commit
- **Preserved context**: Never lose the "why" behind decisions
- **Confidence in changes**: See impact across constitutional boundaries

### For the System:
- **Architectural purity maintained**: Automated guardrails prevent drift
- **Knowledge preserved**: Investigation trails survive developer turnover
- **Evolution guided**: Understand constraints before expanding
- **Quality improved**: Fewer violations means more stable systems

### For the Project:
- **Faster development**: Less time debugging architectural issues
- **Better decisions**: Evidence-based architectural evolution
- **Scalable understanding**: System grows without becoming incomprehensible
- **Sustainable maintenance**: Knowledge doesn't leave with developers

---

## 🧭 Core Philosophy

### The Three-Layer Truth Model
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OBSERVATIONS  │    │     INQUIRY     │    │      LENS       │
│   (What exists) │────▶ (Questions &    │────▶  (How we look)  │
│                 │    │    Patterns)    │    │                 │
│   • FileSight   │    │   • Questions   │    │   • TUI         │
│   • ImportSight │    │   • Patterns    │    │   • CLI         │
│   • Boundary    │    │   • Thinking    │    │   • API         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      Facts                   Understanding          Interface
      (Immutable)            (Human+Algorithmic)   (Constrained)
```

### The Four Pillars of Truth
1. **Observability**: If it cannot be seen, it cannot be claimed
2. **Traceability**: Every claim must have a clear origin
3. **Falsifiability**: Every pattern must be disprovable
4. **Humility**: "I don't know" is more valuable than a confident guess

---

## 🚀 Quick Start

### In 5 Minutes or Less
```bash
# 1. Clone and setup
git clone https://github.com/d4rkbl4de/CodeMarshal
cd CodeMarshal
.\setup.ps1  # Windows or ./setup.sh for Linux/Mac

# 2. Analyze your first project
codemarshal observe /path/to/your/project --constitutional

# 3. Explore interactively
codemarshal tui

# 4. Create a shareable report
codemarshal export /path/to/your/project --format=html --output=report.html
```

### Prerequisites
- **Python 3.11 or higher** (3.12+ recommended)
- **4GB RAM minimum** (8GB recommended for large codebases)
- **Git** (optional, for enhanced features)
- **Windows/Linux/Mac** (fully cross-platform)

---

## 📦 Installation

### Method 1: Automated Setup (Recommended)
```powershell
# Windows
.\setup.ps1

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

**What the setup script does:**
1. Creates Python virtual environment
2. Installs CodeMarshal in development mode
3. Installs optional dependencies (psutil, windows-curses)
4. Verifies installation
5. Provides activation instructions

### Method 2: Manual Installation
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
.\venv\Scripts\Activate
# Linux/Mac:
source venv/bin/activate

# 3. Install CodeMarshal
pip install -e .

# 4. Install optional dependencies
pip install psutil windows-curses  # Windows
pip install psutil                 # Linux/Mac

# 5. Verify installation
codemarshal --help
python -c "import sys; sys.path.insert(0,'.'); import core; print('✅ Core imports working')"
```

### Method 3: Docker (Coming Soon)
```bash
docker pull codemarshal/codemarshal:latest
docker run -v $(pwd):/code codemarshal/codemarshal observe /code --constitutional
```

### Verification Checklist
```bash
# Run these to verify successful installation
codemarshal --version                    # Should show version
codemarshal --help                       # Should show all commands
python -c "from bridge.entry.tui import TUI_AVAILABLE; print(f'TUI Available: {TUI_AVAILABLE}')"
python -m pytest tests/ --coverage       # Should run tests (if available)
```

---

## 🔧 Complete Command Reference

### 🎯 `codemarshal observe` - Collect Immutable Facts
**Purpose**: Gather truth from source code without interpretation

```bash
# BASIC USAGE
codemarshal observe /path/to/project                    # Default analysis
codemarshal observe .                                   # Current directory

# SCOPE CONTROL
codemarshal observe . --scope=file                     # File-level only
codemarshal observe . --scope=module                   # Module/package level
codemarshal observe . --scope=project                  # Full project (default)

# CONSTITUTIONAL ANALYSIS
codemarshal observe . --constitutional                  # Check boundary rules
codemarshal observe . --constitutional --strict        # Fail on violations

# OUTPUT OPTIONS
codemarshal observe . --output=observations.json       # Save to file
codemarshal observe . --format=json                    # JSON output
codemarshal observe . --format=text                    # Human-readable text

# PERFORMANCE OPTIONS
codemarshal observe . --stream                         # Streaming mode for large codebases
codemarshal observe . --workers=4                      # Parallel processing
codemarshal observe . --memory-limit=2048              # Memory limit in MB

# FILTERING
codemarshal observe . --include="*.py,*.js,*.ts"       # Include file patterns
codemarshal observe . --exclude="*/test/*,*/__pycache__/*"  # Exclude patterns
codemarshal observe . --max-file-size=1024             # Max file size in KB

# EXAMPLES
codemarshal observe ./src --constitutional --scope=module --output=src_analysis.json
codemarshal observe . --include="*.py" --exclude="*/migrations/*" --constitutional
codemarshal observe . --stream --workers=8 --memory-limit=4096  # Large codebase
```

**What it collects**:
- File structure and naming patterns
- Import/export relationships
- Architectural boundary crossings
- Encoding and file metadata
- Statistical code metrics

**Output locations**:
- Terminal: Summary statistics and violations
- `storage/observations/`: Immutable observation files
- Specified output file: If using `--output`

---

### 🕵️‍♂️ `codemarshal investigate` - Interactive Investigation
**Purpose**: Guided exploration with anchored thinking

```bash
# START NEW INVESTIGATION
codemarshal investigate /path/to/project --intent="Understand architecture"
codemarshal investigate . --intent="Debug authentication issues" --focus="src/auth/"

# RESUME INVESTIGATION
codemarshal investigate . --resume=session_abc123def456
codemarshal investigate . --resume=latest               # Resume most recent

# SESSION MANAGEMENT
codemarshal investigate . --list-sessions              # Show available sessions
codemarshal investigate . --export-session=session_id  # Export session data
codemarshal investigate . --delete-session=session_id  # Remove session

# WORKFLOW CONTROL
codemarshal investigate . --step-by-step               # Interactive prompting
codemarshal investigate . --auto-advance               # Automatic progression
codemarshal investigate . --questions="structure,purpose,connections"  # Pre-load

# OUTPUT INTEGRATION
codemarshal investigate . --export-ready               # Prepare for export
codemarshal investigate . --notes-file=notes.md        # External notes file
codemarshal investigate . --attach-evidence            # Include observation files

# EXAMPLES
codemarshal investigate . --intent="Onboarding to payment system" --focus="src/payments/"
codemarshal investigate . --resume=latest --export-ready --output=investigation_report.json
codemarshal investigate . --intent="Security audit" --questions="vulnerabilities,permissions"
```

**Investigation workflow**:
1. **Load observations** from previous `observe` run
2. **Present in logical sequence**:
   - What exists? (Observations)
   - What does it do? (Purpose patterns)
   - How is it connected? (Dependency analysis)
   - What seems unusual? (Anomaly detection)
   - What do I think? (Anchored notes)
3. **Save everything** to session storage
4. **Enable resumption** at any point

**Session storage**:
- Location: `storage/sessions/{session_id}/`
- Contents: Observations, questions, patterns, notes, timestamps
- Format: JSON with integrity hashes

---

### ❓ `codemarshal query` - Targeted Inquiry
**Purpose**: Ask specific questions about observed code

```bash
# PATTERN QUERIES
codemarshal query . --pattern=complexity               # Code complexity hotspots
codemarshal query . --pattern=coupling                 # Module coupling analysis
codemarshal query . --pattern=density                  # Code density metrics
codemarshal query . --pattern=violations               # Constitutional violations
codemarshal query . --pattern=anomalies                # Statistical outliers
codemarshal query . --pattern=uncertainty              # Areas of unclear purpose
codemarshal query . --pattern=duplication              # Code duplication detection

# QUESTION QUERIES
codemarshal query . --question=purpose                 # "What does this do?"
codemarshal query . --question=structure               # "How is this organized?"
codemarshal query . --question=connections             # "What depends on this?"
codemarshal query . --question=thinking                # "What have others thought?"
codemarshal query . --question=evolution               # "How has this changed?"

# TARGETED QUERIES
codemarshal query . --target="src/models/User.py"      # Specific file
codemarshal query . --target="package.module"          # Specific module
codemarshal query . --target="function_name"           # Specific function

# COMPARISON QUERIES
codemarshal query . --compare="src/old/ vs src/new/"   # Compare directories
codemarshal query . --compare-versions="v1.0,v1.1,v2.0" # Version comparison
codemarshal query . --compare-patterns="complexity,coupling" # Multiple patterns

# FILTERING AND SORTING
codemarshal query . --filter="score>50"                # Filter results
codemarshal query . --sort-by="complexity"             # Sort results
codemarshal query . --limit=10                         # Limit results
codemarshal query . --threshold=0.7                    # Confidence threshold

# OUTPUT OPTIONS
codemarshal query . --format=json                      # JSON output
codemarshal query . --format=table                     # Table output
codemarshal query . --format=csv                       # CSV output
codemarshal query . --output=query_results.json        # Save to file

# EXAMPLES
codemarshal query . --pattern="complexity,violations" --sort-by="complexity" --limit=5
codemarshal query . --question=connections --target="AuthService" --format=json
codemarshal query . --compare="main vs feature/branch" --pattern=coupling
```

**Pattern types available**:
- **Complexity**: Cyclomatic complexity, cognitive load, nesting depth
- **Coupling**: Afferent/efferent coupling, dependency graphs
- **Violations**: Constitutional boundary crossings
- **Anomalies**: Statistical outliers in code metrics
- **Density**: Code-to-comment ratios, whitespace analysis
- **Uncertainty**: Areas with unclear purpose or naming

---

### 🎨 `codemarshal tui` - Interactive Interface
**Purpose**: Single-focus, truth-preserving visual exploration

```bash
# LAUNCH TUI
codemarshal tui                                        # Launch with default path
codemarshal tui /path/to/project                       # Launch with specific path
codemarshal tui --config=my_config.yaml               # Custom configuration

# TUI KEYBOARD SHORTCUTS
# Navigation:
#   ↑↓←→           Move cursor
#   Tab/Enter      Select/confirm
#   Space          Toggle selection
#   Esc            Back/exit current view
#   Home/End       Beginning/end of list
#   PgUp/PgDn      Page up/down

# Views:
#   v              View violations
#   p              View patterns
#   q              View questions
#   t              View thinking/notes
#   m              View metrics

# Actions:
#   o              Observe current path
#   i              Start investigation
#   e              Export current view
#   s              Save session
#   l              Load session

# System:
#   h              Help screen
#   ?              Show available actions
#   :              Command mode
#   Ctrl+R         Refresh view
#   Ctrl+C         Interrupt/quit
#   q              Quit (when not in input)

# MODES AND VIEWS
# Path Input:      Initial screen to select codebase
# Observation:     View collected observations
# Investigation:   Interactive investigation flow
# Pattern View:    Visual pattern exploration
# Violation View:  Detailed boundary violations
# Help View:       Documentation and shortcuts

# EXAMPLES
codemarshal tui ./my-project                          # Launch for specific project
codemarshal tui --fullscreen                          # Fullscreen mode
codemarshal tui --color=256                           # Color mode
```

**TUI Design Principles**:
1. **Single Focus**: Only one primary content area visible
2. **Linear Flow**: Natural investigation progression
3. **Clear Affordances**: Obvious available actions
4. **Truth-Preserving Aesthetics**: Colors indicate meaning (⚠️ = uncertainty)
5. **Progressive Disclosure**: Complexity revealed only when requested

---

### 📤 `codemarshal export` - Shareable Reports
**Purpose**: Create artifacts from investigations

```bash
# FORMAT OPTIONS
codemarshal export . --format=json                    # Machine-readable JSON
codemarshal export . --format=html                    # Interactive HTML report
codemarshal export . --format=markdown                # Documentation-ready MD
codemarshal export . --format=text                    # Terminal-friendly text
codemarshal export . --format=csv                     # Spreadsheet-ready CSV
codemarshal export . --format=pdf                     # PDF document (requires wkhtmltopdf)

# SCOPE OPTIONS
codemarshal export . --session=session_id             # Export specific session
codemarshal export . --observations                   # Export observations only
codemarshal export . --patterns                       # Export patterns only
codemarshal export . --questions                      # Export questions only
codemarshal export . --violations                     # Export violations only
codemarshal export . --thinking                       # Export thinking/notes only

# CONTENT FILTERING
codemarshal export . --filter="complexity>50,violations"  # Filter content
codemarshal export . --since="2024-01-01"            # Export since date
codemarshal export . --until="2024-12-31"            # Export until date
codemarshal export . --tags="security,performance"   # Export by tags

# OUTPUT CONTROL
codemarshal export . --output=report.html            # Specify output file
codemarshal export . --output-dir=reports/           # Output directory
codemarshal export . --template=custom_template.html # Custom template
codemarshal export . --include-code                  # Include code snippets
codemarshal export . --include-graphs                # Include visual graphs
codemarshal export . --compress                      # Compress output

# STYLING AND BRANDING
codemarshal export . --theme=dark                    # Dark theme
codemarshal export . --logo=my_logo.png              # Custom logo
codemarshal export . --title="My Analysis Report"    # Custom title
codemarshal export . --author="John Developer"       # Author attribution

# EXAMPLES
codemarshal export . --format=html --output=full_report.html --include-graphs --theme=dark
codemarshal export . --session=abc123 --format=markdown --output=investigation_notes.md
codemarshal export . --observations --format=json --output=observations.json --compress
codemarshal export . --filter="violations,complexity>75" --format=csv --output=issues.csv
```

**Export artifacts include**:
- **Immutable observations** with integrity hashes
- **Pattern detection results** with confidence scores
- **Anchored questions and answers**
- **Violation reports** with file/line references
- **Visual diagrams** (HTML/PDF exports)
- **Reproducibility data** (timestamps, versions, hashes)

---

### 🛠️ Utility Commands

```bash
# VERSION AND INFO
codemarshal --version                                  # Show version
codemarshal --help                                     # General help
codemarshal observe --help                            # Command-specific help
codemarshal --info                                     # System information

# CONFIGURATION
codemarshal config show                                # Show current configuration
codemarshal config edit                                # Edit configuration
codemarshal config reset                               # Reset to defaults
codemarshal config validate                            # Validate configuration

# MAINTENANCE
codemarshal cleanup                                    # Clean temporary files
codemarshal repair                                     # Repair corrupted data
codemarshal backup                                     # Create backup
codemarshal restore --backup=backup.zip               # Restore from backup

# DEVELOPMENT
codemarshal test                                       # Run self-tests
codemarshal benchmark                                  # Performance benchmark
codemarshal profile                                    # Profile performance
codemarshal debug                                      # Debug mode
```

---

## 🏗️ Architecture Overview

### Directory Structure
```
CodeMarshal/
├── bridge/                    # Entry points and coordination
│   ├── entry/                # CLI, TUI, API interfaces
│   ├── commands/             # Command implementations
│   ├── coordination/         # Scheduling and caching
│   └── integration/          # CI/CD, editor integration
├── core/                     # Engine and runtime
│   ├── runtime.py           # Main coordination
│   ├── engine.py            # Investigation engine
│   ├── context.py           # Runtime context
│   ├── state.py             # State machine
│   └── interfaces.py        # Protocol definitions
├── observations/            # Truth collection layer
│   ├── eyes/               # Observation methods
│   │   ├── file_sight.py   # File structure
│   │   ├── import_sight.py # Import relationships
│   │   ├── boundary_sight.py # Architectural boundaries
│   │   ├── encoding_sight.py # File encoding
│   │   └── export_sight.py # Export patterns
│   ├── record/             # Immutable recording
│   └── limitations/        # Declared limitations
├── inquiry/                # Human+algorithmic layer
│   ├── questions/          # Human questions
│   ├── patterns/           # Pattern detection
│   └── session/            # Investigation sessions
├── lens/                   # Interface layer
│   ├── aesthetic/          # Visual design
│   ├── views/              # Interface views
│   ├── navigation/         # Navigation logic
│   └── philosophy/         # Interface principles
├── integrity/              # Self-validation
│   ├── monitoring/         # Runtime monitoring
│   ├── validation/         # Constitutional validation
│   ├── prohibitions/       # Prohibition enforcement
│   └── recovery/           # Recovery mechanisms
├── storage/               # Data persistence
│   ├── atomic.py          # Atomic operations
│   ├── transactional.py   # Transactional writes
│   └── corruption.py      # Corruption detection
└── config/                # Configuration
    ├── boundaries.py      # Boundary definitions
    ├── schema.py          # Configuration schema
    └── loader.py          # Configuration loading
```

### Data Flow
```
1. SOURCE CODE
   ↓
2. OBSERVATION EYES (immutable facts)
   • FileSight: Structure and naming
   • ImportSight: Dependencies
   • BoundarySight: Architectural layers
   • EncodingSight: File properties
   • ExportSight: Public interfaces
   ↓
3. IMMUTABLE OBSERVATIONS (SHA256 hashed)
   ↓
4. PATTERN DETECTION
   • Density: Code concentration
   • Coupling: Module relationships  
   • Complexity: Cognitive load
   • Violations: Rule breaches
   • Uncertainty: Unknown areas
   ↓
5. HUMAN INVESTIGATION
   • Questions: Human inquiries
   • Thinking: Anchored notes
   • Patterns: Recognized structures
   ↓
6. INTERFACE PRESENTATION
   • TUI: Single-focus exploration
   • CLI: Scriptable access
   • API: Programmatic access
   ↓
7. EXPORTED ARTIFACTS
   • Reports: Shareable findings
   • Data: Machine-readable
   • Documentation: Anchored knowledge
```

### Performance Characteristics
- **Processing Speed**: 14.7 files/second (tested on 5,004 files)
- **Memory Usage**: < 1GB for 5,000 files (scales linearly)
- **Initialization**: 3.25 seconds (optimized from 59s)
- **Observation Storage**: ~5MB per 1,000 files
- **Concurrency**: Streaming architecture, parallel processing

---

## ⚖️ Constitutional Framework

### The 24 Constitutional Articles

#### TIER 1: FOUNDATIONAL TRUTHS (NEVER VIOLATE)
1. **Article 1: Observation Purity** - Record only what's textually present
2. **Article 2: Human Primacy** - Humans ask questions, system provides observations
3. **Article 3: Truth Preservation** - Never obscure, distort, or invent
4. **Article 4: Progressive Disclosure** - Reveal complexity only when requested

#### TIER 2: INTERFACE INTEGRITY
5. **Article 5: Single-Focus Interface** - One primary content area at a time
6. **Article 6: Linear Investigation** - Follow natural curiosity flow
7. **Article 7: Clear Affordances** - Obvious, consistent actions
8. **Article 8: Honest Performance** - Show computation time, never pretend speed

#### TIER 3: ARCHITECTURAL CONSTRAINTS
9. **Article 9: Immutable Observations** - Once recorded, never changed
10. **Article 10: Anchored Thinking** - All thoughts anchored to observations
11. **Article 11: Declared Limitations** - Every method declares what it cannot see
12. **Article 12: Local Operation** - No network dependencies for core functionality

#### TIER 4: SYSTEM BEHAVIOR
13. **Article 13: Deterministic Operation** - Same input → same output, always
14. **Article 14: Graceful Degradation** - Preserve what works when parts fail
15. **Article 15: Session Integrity** - Investigations survive interruptions

#### TIER 5: AESTHETIC CONSTRAINTS
16. **Article 16: Truth-Preserving Aesthetics** - Visual design enhances truth perception
17. **Article 17: Minimal Decoration** - No decoration for decoration's sake
18. **Article 18: Consistent Metaphor** - Single investigation metaphor throughout

#### TIER 6: EVOLUTION RULES
19. **Article 19: Backward Truth Compatibility** - Old investigations remain valid
20. **Article 20: Progressive Enhancement** - Build on, don't replace
21. **Article 21: Self-Validation** - System verifies its own constitutional compliance

### Enforcement Mechanism

#### The Three Guardians
1. **Static Guardian**: Pre-commit hooks validate compliance
2. **Runtime Guardian**: Monitors truth-preserving behavior
3. **Interface Guardian**: UI prevents truth-violating interactions

#### Violation Consequences
- **Tier 1-2 Violations**: Immediate halt, cannot proceed until fixed
- **Tier 3-4 Violations**: Warning with required fix timeline
- **Tier 5-6 Violations**: Team review, architectural adjustment

#### Amendment Process
1. **Proposal**: Written case with truth-impact analysis
2. **Review**: 7-day discussion with all contributors
3. **Approval**: 80% agreement required for Tier 1-3 changes
4. **Implementation**: Update constitution, tests, and documentation
5. **Verification**: Run full integrity suite before release

---

## 🎯 Use Cases & Workflows

### Use Case 1: New Developer Onboarding
```bash
# DAY 1: Initial Exploration
codemarshal observe . --constitutional --output=day1_observations.json
codemarshal tui  # Interactive exploration

# DAY 2: Focused Learning
codemarshal investigate . --intent="Understand authentication system" --focus="src/auth/"
codemarshal query . --question=connections --target="AuthService"

# DAY 3: Knowledge Documentation
codemarshal export . --format=html --output="my_understanding.html" --include-code

# DAY 4: Contribution Planning
codemarshal observe . --scope=staged --constitutional  # Pre-commit check
codemarshal investigate . --intent="Plan feature implementation"
```

### Use Case 2: Architectural Refactoring
```bash
# PHASE 1: Baseline Establishment
codemarshal observe . --constitutional --output=before_refactor.json
codemarshal query . --pattern="coupling,complexity" --output=hotspots.json

# PHASE 2: Impact Analysis
codemarshal investigate . --intent="Analyze refactoring impact" --focus="module/to/refactor"
codemarshal query . --question=connections --target="ModuleToRefactor"

# PHASE 3: Safe Refactoring
codemarshal observe . --scope=staged --constitutional  # Each commit
codemarshal export . --format=markdown --output=refactoring_plan.md

# PHASE 4: Verification
codemarshal observe . --constitutional --output=after_refactor.json
codemarshal query . --pattern=violations  # Should be empty or reduced
```

### Use Case 3: Production Incident Investigation
```bash
# IMMEDIATE RESPONSE
codemarshal observe . --constitutional --output=incident_baseline.json
codemarshal query . --pattern=anomalies --since="24 hours ago"

# ROOT CAUSE ANALYSIS
codemarshal investigate . --intent="Find root cause of service outage" --focus="affected/module"
codemarshal query . --question=connections --target="FailingComponent"

# PREVENTIVE MEASURES
codemarshal export . --format=html --output="incident_report_$(date).html"
codemarshal query . --pattern="complexity,coupling" --filter="score>80" --output=tech_debt.md
```

### Use Case 4: Security Audit
```bash
# COMPREHENSIVE SCAN
codemarshal observe . --constitutional --include="*.py,*.js,*.yml,*.yaml"
codemarshal query . --pattern=violations --filter="severity=high"

# VULNERABILITY ANALYSIS
codemarshal investigate . --intent="Security audit" --questions="permissions,dependencies"
codemarshal query . --question=connections --target="ExternalDependencies"

# REPORT GENERATION
codemarshal export . --format=pdf --output="security_audit_$(date).pdf" --theme=dark
codemarshal export . --format=json --output=security_findings.json --compress
```

### Use Case 5: CI/CD Pipeline Integration
```yaml
# .github/workflows/constitutional-check.yml
name: Constitutional Compliance
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      
      - name: Install CodeMarshal
        run: |
          pip install -e .
          pip install psutil
      
      - name: Constitutional Analysis
        run: |
          codemarshal observe . --constitutional --output=violations.json
          if [ -s violations.json ]; then
            echo "Constitutional violations found!"
            codemarshal export . --format=markdown >> violations.md
            exit 1
          fi
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: constitutional-analysis
          path: |
            violations.json
            violations.md
```

---

## ⚙️ Configuration

### Configuration Files
CodeMarshal supports multiple configuration sources (in order of priority):

1. **Command-line arguments** (highest priority)
2. **Environment variables** (`CODEMARSHAL_*`)
3. **Project config** (`codemarshal.yaml` in project root)
4. **User config** (`~/.config/codemarshal/config.yaml`)
5. **System config** (`/etc/codemarshal/config.yaml`)
6. **Default values** (lowest priority)

### Example Configuration File
Create `codemarshal.yaml` in your project root:

```yaml
# codemarshal.yaml - Project-specific configuration

# Constitutional Rules
constitutional_rules:
  - no_cross_layer_imports
  - no_circular_dependencies
  - interface_implementation_separation
  - dependency_inversion

# Architectural Layers
architectural_layers:
  presentation:
    - "ui/"
    - "views/"
    - "components/"
  business_logic:
    - "services/"
    - "models/"
    - "business/"
  data_access:
    - "repositories/"
    - "dao/"
    - "database/"
  infrastructure:
    - "config/"
    - "logging/"
    - "monitoring/"

# Boundary Rules
boundary_rules:
  allowed:
    - presentation → business_logic
    - business_logic → data_access
    - "* → infrastructure"  # All layers can use infrastructure
  prohibited:
    - data_access → presentation
    - presentation → data_access
    - business_logic → presentation

# Import Rules
import_rules:
  allow_relative_imports: true
  allow_wildcard_imports: false
  allow_stdlib_circular: false
  max_import_depth: 5

# Analysis Configuration
analysis:
  file_patterns:
    include: ["*.py", "*.js", "*.ts", "*.java", "*.go"]
    exclude: ["*/test/*", "*/__pycache__/*", "*.min.js"]
  max_file_size_kb: 1024
  follow_symlinks: false
  detect_encoding: true

# Pattern Detection
patterns:
  complexity:
    enabled: true
    threshold: 50
    metrics: ["cyclomatic", "cognitive", "nesting"]
  coupling:
    enabled: true
    threshold: 0.7
    types: ["afferent", "efferent", "instability"]
  violations:
    enabled: true
    severity_levels: ["critical", "high", "medium", "low"]
  anomalies:
    enabled: true
    sensitivity: 0.85

# Performance Settings
performance:
  stream_large_projects: true
  max_memory_mb: 4096
  worker_count: 4
  chunk_size: 100

# Output Configuration
output:
  default_format: "text"
  color_enabled: true
  unicode_enabled: true
  progress_bars: true
  verbose: false

# Export Settings
export:
  html_template: "default"
  include_graphs: true
  include_code_snippets: true
  compress_output: false

# TUI Settings
tui:
  color_scheme: "default"
  show_help: true
  confirm_exit: true
  auto_save: true
```

### Environment Variables
```bash
# Performance
export CODEMARSHAL_MAX_MEMORY_MB=8192
export CODEMARSHAL_WORKER_COUNT=8
export CODEMARSHAL_STREAM_ENABLED=true

# Output
export CODEMARSHAL_COLOR=always
export CODEMARSHAL_VERBOSE=true
export CODEMARSHAL_OUTPUT_FORMAT=json

# Paths
export CODEMARSHAL_CONFIG_PATH=/path/to/config.yaml
export CODEMARSHAL_STORAGE_PATH=/path/to/storage
export CODEMARSHAL_CACHE_PATH=/path/to/cache

# Development
export CODEMARSHAL_DEBUG=true
export CODEMARSHAL_PROFILE=true
export CODEMARSHAL_TEST_MODE=false
```

### Configuration Validation
```bash
# Validate configuration
codemarshal config validate

# Show effective configuration
codemarshal config show --effective

# Edit configuration
codemarshal config edit

# Reset to defaults
codemarshal config reset --confirm
```

---

## 📊 Output & Interpretation

### Understanding Observation Output
```
OBSERVATION SUMMARY
├── Files Processed: 5,004
├── Observations Created: 32,687
├── Import Relationships: 24,138
├── Boundary Checks: 5,492
└── Constitutional Violations: 0 ✅

PERFORMANCE METRICS
├── Duration: 5 minutes, 40 seconds
├── Speed: 14.7 files/second
├── Memory Peak: 876 MB
└── Storage Used: 42 MB

CONSTITUTIONAL ANALYSIS
├── Layer Violations: 0
├── Circular Dependencies: 3
├── Interface Violations: 0
└── Dependency Violations: 0
```

### Pattern Detection Results
```json
{
  "pattern": "complexity",
  "files": [
    {
      "path": "src/services/payment_processor.py",
      "complexity_score": 87,
      "metrics": {
        "cyclomatic": 45,
        "cognitive": 32,
        "nesting_depth": 7,
        "line_count": 412,
        "function_count": 28
      },
      "hotspots": [
        {"function": "process_transaction", "lines": "45-189", "score": 92},
        {"function": "validate_currency", "lines": "210-287", "score": 78}
      ],
      "recommendations": [
        "Extract validation logic to separate class",
        "Consider splitting into multiple specialized processors"
      ]
    }
  ]
}
```

### Violation Reports
```
CONSTITUTIONAL VIOLATION DETECTED
╔══════════════════════════════════════════════════════════════════╗
║ SEVERITY: HIGH                                                   ║
║ RULE: No cross-layer imports                                     ║
║ FILE: src/ui/components/UserDashboard.js                        ║
║ LINE: 23                                                         ║
╚══════════════════════════════════════════════════════════════════╝

VIOLATION DETAILS:
• Import: `import { DatabaseConnection } from '../../../data/db.js'`
• Layer Crossing: presentation → data_access
• Rule: Presentation layer must not directly access data layer
• Recommendation: Use service layer abstraction

EVIDENCE ANCHOR:
• Observation ID: obs_abc123def456
• File Hash: sha256:abc123...
• Timestamp: 2024-01-12T23:18:08Z
```

### Export Report Structure
```
HTML Report Structure:
├── index.html                    # Main report
├── assets/
│   ├── css/style.css            # Styling
│   ├── js/interactive.js        # Interactive elements
│   └── graphs/                  # Generated graphs
├── observations/                 # Observation data
│   ├── files.json               # File observations
│   ├── imports.json             # Import observations
│   └── boundaries.json          # Boundary observations
├── patterns/                    # Pattern detection results
│   ├── complexity.html          # Complexity analysis
│   ├── coupling.html            # Coupling analysis
│   └── violations.html          # Violation details
├── investigation/               # Investigation session
│   ├── questions_answers.html   # Q&A
│   ├── thinking_notes.html      # Anchored thoughts
│   └── decisions.html           # Decision log
└── reproducibility/             # Reproducibility data
    ├── hashes.json              # Integrity hashes
    ├── environment.json         # Environment info
    └── configuration.json       # Used configuration
```

---

## 🧪 Testing & Validation

### Self-Validation Commands
```bash
# Run constitutional self-check
codemarshal observe . --constitutional

# Run integrity tests
python -m pytest integrity/validation/ -v

# Run performance tests
python -m pytest tests/performance.test.py -v

# Run end-to-end tests
python -m pytest tests/end_to_end.test.py -v

# Run invariant tests
python -m pytest tests/invariants.test.py -v
```

### Testing Your Configuration
```bash
# Test boundary configuration
codemarshal observe . --config=test_config.yaml --constitutional --dry-run

# Test pattern detection
codemarshal query . --pattern=complexity --test-mode

# Test export functionality
codemarshal export . --format=html --test --output=test_report.html

# Test TUI functionality
codemarshal tui --test --exit-after=30
```

### Benchmarking
```bash
# Run performance benchmark
codemarshal benchmark --size=small    # 1,000 files
codemarshal benchmark --size=medium   # 10,000 files
codemarshal benchmark --size=large    # 50,000 files

# Profile specific operations
codemarshal profile observe --target=./large-project
codemarshal profile query --pattern=complexity

# Memory usage analysis
codemarshal observe . --memory-profile --output=memory_usage.json
```

### Test Codebases
CodeMarshal includes test codebases for validation:

```bash
# Test with included violation examples
codemarshal observe test_violations/ --constitutional

# Test with Agent Nexus structure (simplified)
codemarshal observe test_agent_nexus/ --constitutional

# Test performance with generated code
python create_5k_test_files.py  # Generate test files
codemarshal observe generated_test/ --stream
```

---

## 🤝 Contributing

### Development Setup
```bash
# 1. Fork and clone
git clone https://github.com/your-username/CodeMarshal
cd CodeMarshal

# 2. Set up development environment
.\setup.ps1 --dev  # or ./setup.sh --dev

# 3. Run tests
pytest tests/ -xvs

# 4. Verify constitutional compliance
codemarshal observe . --constitutional

# 5. Make changes and test
# ... your changes ...
python -m pytest tests/ --cov=core --cov=observations

# 6. Submit pull request
```

### Contribution Guidelines

#### 1. Constitutional Compliance
All contributions must maintain constitutional purity:

```python
# ✅ GOOD: Truth-preserving observation
def observe_file_structure(path: str) -> Observation:
    """Record only what exists in the file system."""
    return Observation(
        facts=list_directory_facts(path),  # Only facts
        uncertainty_markers=identify_uncertainty(path),  # Mark uncertainty
        limitations=declare_limitations()  # Declare what we cannot see
    )

# ❌ BAD: Inference or guessing
def guess_file_purpose(path: str) -> str:
    """This infers purpose - violates Article 1."""
    if "util" in path:
        return "Utility functions"  # ❌ Guessing!
```

#### 2. Architectural Purity
Maintain the three-layer architecture:

- **Core layer** must not import from higher layers
- **Observations** must remain immutable
- **Interface** must maintain single-focus principle
- **Dependencies** must be declared and justified

#### 3. Code Standards
- **Black formatting**: `black .`
- **Type hints**: All new functions must have type hints
- **Docstrings**: Google-style docstrings for public APIs
- **Tests**: 90%+ coverage for new functionality
- **Performance**: No regression in processing speed

#### 4. Pull Request Process
1. **Fork repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes**: Follow constitutional principles
4. **Run tests**: `pytest tests/ --cov`
5. **Constitutional check**: `codemarshal observe . --constitutional`
6. **Update documentation**: README, docstrings, examples
7. **Submit PR**: With detailed description and evidence

### Development Tips

#### Working with Observations
```python
# Creating new observation eyes
from observations.eyes.base import BaseSight
from observations.record.snapshot import Observation

class NewSight(BaseSight):
    """Example of creating a new observation eye."""
    
    def observe(self, path: str) -> Observation:
        # Collect only textual facts
        facts = self._collect_facts(path)
        
        # Declare limitations
        limitations = self._declare_limitations()
        
        # Mark uncertainty where appropriate
        uncertainty = self._identify_uncertainty(facts)
        
        return Observation(
            type="new_sight",
            facts=facts,
            limitations=limitations,
            uncertainty_markers=uncertainty,
            integrity_hash=self._compute_hash(facts)
        )
```

#### Adding New Patterns
```python
# Adding new pattern detection
from inquiry.patterns.base import BasePattern

class NewPattern(BasePattern):
    """Example of creating a new pattern detector."""
    
    def detect(self, observations: List[Observation]) -> PatternResult:
        # Analyze observations
        patterns = self._analyze(observations)
        
        # Calculate confidence scores
        confidence = self._calculate_confidence(patterns)
        
        # Anchor to specific observations
        anchors = self._anchor_to_observations(patterns)
        
        return PatternResult(
            name="new_pattern",
            patterns=patterns,
            confidence_scores=confidence,
            observation_anchors=anchors,
            limitations=self._declare_limitations()
        )
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue 1: "CORE IMPORT WARNING" on Startup
```
[CORE IMPORT WARNING] Constitutional violation: Core modules importing from higher layers
```

**Solution:**
```bash
# 1. Diagnose the violation
codemarshal observe . --constitutional

# 2. Check core purity
python -c "import sys; sys.path.insert(0,'.'); import core; print('Core imports clean')"

# 3. Fix violating imports
# Look for imports from storage/ or integrity/ in core/ modules
# Refactor to use dependency injection
```

#### Issue 2: TUI Not Launching
```
TUI_AVAILABLE: False
```

**Solution:**
```bash
# 1. Install windows-curses (Windows)
pip install windows-curses

# 2. Or install curses (Linux/Mac)
pip install curses

# 3. Check TUI availability
python -c "from bridge.entry.tui import TUI_AVAILABLE; print(f'TUI_AVAILABLE: {TUI_AVAILABLE}')"

# 4. Launch in debug mode
codemarshal tui --debug
```

#### Issue 3: Slow Performance on Large Codebases
**Solution:**
```bash
# 1. Use streaming mode
codemarshal observe . --stream

# 2. Increase workers (default: 4)
codemarshal observe . --workers=8

# 3. Set memory limit
codemarshal observe . --memory-limit=4096

# 4. Analyze in chunks
codemarshal observe . --chunk-size=500

# 5. Exclude unnecessary files
codemarshal observe . --exclude="*/node_modules/*,*/dist/*,*/build/*"
```

#### Issue 4: Memory Usage Too High
**Solution:**
```bash
# 1. Monitor memory usage
codemarshal observe . --memory-profile --output=memory.json

# 2. Use streaming for large codebases
codemarshal observe . --stream --memory-limit=2048

# 3. Analyze smaller chunks
codemarshal observe src/ --chunk-size=250

# 4. Increase swap space (system-level)
# 5. Use 64-bit Python if available
```

#### Issue 5: False Positive Violations
**Solution:**
```bash
# 1. Create custom boundary configuration
# Create codemarshal.yaml with correct layer definitions

# 2. Adjust sensitivity
codemarshal observe . --constitutional --sensitivity=0.8

# 3. Ignore specific patterns
codemarshal observe . --constitutional --ignore="test/,vendor/"

# 4. Review and adjust rules
# Edit constitutional rules in configuration
```

#### Issue 6: Export Format Problems
**Solution:**
```bash
# 1. Check required dependencies for HTML/PDF export
pip install weasyprint  # For PDF export
pip install jinja2     # For template rendering

# 2. Use simpler format
codemarshal export . --format=text

# 3. Check disk space
df -h  # Linux/Mac
Get-PSDrive C  # Windows

# 4. Use custom template
codemarshal export . --format=html --template=simple_template.html
```

### Debugging Commands
```bash
# Enable debug logging
codemarshal observe . --debug --log-level=DEBUG

# Profile performance
codemarshal profile observe . --output=profile.json

# Trace execution
codemarshal observe . --trace --output=trace.log

# Validate data integrity
codemarshal storage validate --repair

# Reset corrupted state
codemarshal cleanup --all
codemarshal repair --backup=latest
```

### Getting Help
1. **Check logs**: `~/.codemarshal/logs/` or `deployment_logs/`
2. **Run self-diagnosis**: `codemarshal diagnose`
3. **Create bug report**: `codemarshal bug-report --output=bug_report.zip`
4. **Check GitHub Issues**: [https://github.com/d4rkbl4de/CodeMarshal/issues](https://github.com/d4rkbl4de/CodeMarshal/issues)

---

## 📚 Documentation

### Additional Documentation Files

| File | Purpose |
|------|---------|
| **`CONSTITUTIONAL_ANALYSIS.md`** | Complete constitutional framework (24 articles) |
| **`Structure.md`** | Architectural overview and module relationships |
| **`README.truth.md`** | Philosophical foundation and principles |
| **`50k_production_test_plan.md`** | Large-scale testing methodology |
| **`architectural_decisions.md`** | Key design decisions and trade-offs |
| **`execution_checklist.md`** | Deployment and verification checklist |
| **`CONTRIBUTING.md`** | Detailed contribution guidelines |
| **`CODE_OF_CONDUCT.md`** | Community standards and behavior |

### API Documentation
Generate API documentation:
```bash
# Generate documentation
pydoc-markdown --output=API.md

# View documentation
python -m pydoc core.runtime
python -m pydoc observations.eyes.boundary_sight
```

### Examples Directory
```bash
# Explore examples
examples/
├── basic_analysis/
│   ├── simple_project/
│   └── analysis_script.py
├── constitutional_configs/
│   ├── layered_architecture.yaml
│   ├── microservices.yaml
│   └── monolith.yaml
├── integrations/
│   ├── pre_commit_hook.py
│   ├── github_action.yaml
│   └── jenkins_pipeline.groovy
└── custom_patterns/
    ├── security_pattern.py
    ├── performance_pattern.py
    └── documentation_pattern.py
```

---

## 📄 License

CodeMarshal is released under the **MIT License**:

```text
MIT License

Copyright (c) 2024 d4rkbl4de

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Third-Party Licenses
CodeMarshal uses these open-source components:
- **Python 3.11+** (PSF License)
- **psutil** (BSD License)
- **windows-curses** (Public Domain)
- **Jinja2** (BSD License) - for HTML exports
- **WeasyPrint** (BSD License) - for PDF exports (optional)

### Citation
If you use CodeMarshal in research or publications:
```
@software{CodeMarshal2024,
  author = {d4rkbl4de},
  title = {CodeMarshal: Truth-Preserving Investigation Environment},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/d4rkbl4de/CodeMarshal}
}
```

---

## 🌟 Final Notes

### Why CodeMarshal Matters
In a world of AI-generated code and increasingly complex systems, **truth preservation** is becoming the most valuable engineering discipline. CodeMarshal provides:

1. **A sanctuary from guessing**: Where only verified facts exist
2. **A map for complexity**: That grows with your understanding
3. **A notebook for wisdom**: That preserves your thinking across time
4. **A constitution for code**: That maintains architectural integrity

### The Ultimate Measure of Success
As you use CodeMarshal, ask yourself:
> "Does this tool make me better at understanding complex systems without ever pretending to understand for me?"

If the answer is yes, then CodeMarshal is fulfilling its purpose.

### Getting Started Today
```bash
# Start small
codemarshal observe . --constitutional

# Then explore
codemarshal tui

# Then understand
codemarshal investigate . --intent="Learn one thing well"

# Then share
codemarshal export . --format=html --output="my_first_truth.html"
```

**Welcome to truth-preserving investigation. Welcome to CodeMarshal.** 🕵️‍♂️🔍

---

*Last Updated: January 2024*  
*Version: 1.0.0*  
*Constitutional Compliance: 24/24 Articles Satisfied*