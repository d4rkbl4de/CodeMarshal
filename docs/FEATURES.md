# CodeMarshal Features

**Version**: 2.0.0  
**Last Updated**: February 7, 2026

---

## What is CodeMarshal?

**CodeMarshal** is a truth-preserving cognitive investigation environment for understanding complex codebases. Think of it as a "detective's notebook" for your code—it helps you investigate, understand, and maintain architectural integrity without ever lying to you.

Unlike traditional code analysis tools that overwhelm you with data or make guesses using AI, CodeMarshal follows strict constitutional principles to show you **only what actually exists** in your code, anchored to evidence, with clear limitations declared upfront.

---

## 🎯 Core Philosophy

### Truth Preservation

- **Only shows what exists** — no AI hallucinations, no guesses
- **Immutable observations** — once recorded, facts never change
- **Anchored evidence** — every claim tied to specific code locations
- **Declared limitations** — system explicitly states what it cannot see

### Human Primacy

- **You ask the questions** — system never decides for you
- **One question at a time** — no overwhelming dashboards
- **Progressive disclosure** — complexity revealed only when requested
- **Preserved thinking** — your investigation trail is saved

---

## 🚀 Key Features

### 1. 🔍 **Code Investigation**

#### **Observation System**

Collect immutable facts about your codebase through multiple "eyes":

- **FileSight** — File structure, naming conventions, organization
- **ImportSight** — Static import relationships and dependencies
- **BoundarySight** — Architectural layer boundaries and violations
- **EncodingSight** — File encoding, types, and properties
- **ExportSight** — Public interfaces and API surfaces

#### **Query System**

Ask questions about your code and get evidence-based answers:

- Pattern-based queries ("Find all functions over 50 lines")
- Connection queries ("What depends on this module?")
- Anomaly detection ("What looks unusual here?")
- Purpose extraction ("What does this file do?")

#### **Pattern Detection**

Automatically detect code patterns and issues:

- **Security patterns** — Hardcoded passwords, API keys, eval() usage
- **Performance patterns** — Inefficient algorithms, memory leaks
- **Style patterns** — Naming violations, formatting issues
- **Custom patterns** — Define your own detection rules

### 2. 🛠️ **CLI Commands**

#### **Core Investigation**

```bash
codemarshal investigate <path>     # Start a new investigation
codemarshal observe <path>         # Collect observations only
codemarshal query <question>       # Ask specific questions
codemarshal export <format>        # Export investigation results
codemarshal gui                    # Launch desktop GUI
```

#### **Configuration Management** (v2.0)

```bash
codemarshal config show            # Display current configuration
codemarshal config edit            # Edit configuration in $EDITOR
codemarshal config reset           # Reset to default configuration
codemarshal config validate        # Validate configuration file
```

#### **Backup & Restore** (v2.0)

```bash
codemarshal backup create          # Create a backup
codemarshal backup list            # List available backups
codemarshal backup restore <id>    # Restore from backup
codemarshal backup verify <id>     # Verify backup integrity
```

#### **Search** (v2.0)

```bash
codemarshal search <pattern>       # Search codebase with regex
codemarshal search "TODO"          # Find TODO comments
codemarshal search "def " --type=py # Search Python files only
codemarshal search "pattern" --output=json  # Export results as JSON
```

#### **Pattern Detection** (v2.0)

```bash
codemarshal pattern list           # List available patterns
codemarshal pattern scan           # Scan for all patterns
codemarshal pattern scan --category=security  # Security patterns only
codemarshal pattern add --id=my_pattern --pattern="regex"  # Add custom pattern
```

#### **System Maintenance** (v2.0)

```bash
codemarshal cleanup                # Remove temporary files
codemarshal cleanup --dry-run      # Preview what would be cleaned
codemarshal repair                 # Fix corrupted data
codemarshal repair --validate-only # Check without repairing
```

#### **Testing** (v2.0)

```bash
codemarshal test                   # Run test suite
codemarshal test --coverage        # Run with coverage report
codemarshal test --fail-fast       # Stop on first failure
```

#### **System Information**

```bash
codemarshal --version              # Show version information
codemarshal --info                 # Show system diagnostics
codemarshal --help                 # Show help for all commands
```

### 3. 📊 **Export Formats**

Export your investigations in multiple formats:

#### **JSON** ✅

- Machine-readable structured data
- Perfect for programmatic processing
- Preserves full hierarchy

#### **Markdown** ✅

- Human-readable documentation
- Great for GitHub/GitLab
- Includes formatted reports

#### **Plain Text** ✅

- Maximum compatibility
- Simple, readable output
- Works everywhere

#### **HTML** ✅ (v2.0)

- Interactive web reports
- Visual hierarchy with CSS
- Cross-references as hyperlinks
- Print-friendly styles

#### **CSV** ✅ (v2.0)

- Spreadsheet-compatible
- Perfect for data analysis
- Import into Excel/Google Sheets
- Tabular data format

### 4. 🐳 **Docker Support** (v2.0)

#### **Production Container**

- Multi-stage build for smaller image size
- Non-root user for security
- Pre-installed with ripgrep for fast search
- Health checks enabled

#### **Development Container**

- Full development toolchain included
- pytest, black, ruff, mypy pre-installed
- Volume mounts for live development
- Interactive shell support

#### **Docker Compose**

- One-command deployment: `docker-compose up`
- Persistent volume for data
- Separate dev and production configs

### 5. 🔧 **Integrations** (v2.0)

#### **Pre-commit Hooks**

Automatically check code before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/codemarshal/codemarshal
    hooks:
      - id: codemarshal-constitutional
```

Detects:

- Hardcoded secrets
- API keys in code
- Security vulnerabilities
- Architectural violations

#### **GitHub Actions**

Automated CI/CD pipeline:

```yaml
name: CodeMarshal Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Security Scan
        run: codemarshal pattern scan --category=security
      - name: Generate Report
        run: codemarshal export . --format=html --output=report.html
```

#### **Editor Integration** (Foundation)

- VS Code extension support planned
- Vim/Neovim plugin architecture
- Emacs integration hooks

### 6. 🖥 **Desktop GUI** (v2.1)

- **Native PySide6 application** for Windows/Linux/macOS
- **Single-focus workflow**: observe, investigate, patterns, export
- **Dark, high-contrast theme** with detective-inspired typography
- **Local-only operation** (no network dependencies)

### 7. 🎨 **Text User Interface (TUI)**

Interactive terminal interface:

- **Overview View** — High-level system summary
- **Examination View** — Deep dive into specific files
- **Connections View** — Dependency visualization
- **Patterns View** — Pattern detection results
- **Thinking View** — Your notes and thoughts
- **Help View** — Context-sensitive help

Features:

- Keyboard shortcuts for fast navigation
- Color-coded severity levels
- Progress indicators for long operations
- Error recovery and context preservation

### 8. 📦 **Pattern System** (v2.0)

#### **Built-in Patterns**

8 security patterns included:

1. **Hardcoded Password** — Detects password = "..."
2. **Hardcoded API Key** — Detects api_key = "..."
3. **Hardcoded Token** — Detects token = "..."
4. **Private Key** — Detects private key blocks
5. **Dangerous eval()** — Detects eval() usage
6. **Dangerous exec()** — Detects exec() usage
7. **Debug Mode Enabled** — Detects debug = True
8. **HTTP Instead of HTTPS** — Detects http:// URLs

#### **Custom Patterns**

Define your own patterns in YAML:

```yaml
patterns:
  - id: my_custom_check
    name: "My Custom Check"
    pattern: "regex_here"
    severity: warning
    description: "What this pattern detects"
    message: "Found at {{file}}:{{line}}"
    tags: [custom, team-specific]
    languages: [python, javascript]
```

### 9. 🔒 **Constitutional Enforcement**

24 non-negotiable principles enforced automatically:

**Tier 1: Foundational Truths**

- Observation purity (no inference)
- Human primacy (you're in control)
- Truth preservation (never lies)
- Progressive disclosure (not overwhelming)

**Tier 2: Interface Integrity**

- Single-focus interface
- Linear investigation flow
- Clear affordances (obvious actions)
- Honest performance indicators

**Tier 3: Architectural Constraints**

- Immutable observations
- Anchored thinking
- Declared limitations
- Local operation (no network required)

**Tier 4: System Behavior**

- Graceful degradation
- Resource transparency
- Error honesty
- Recovery capability

**Tier 5: Quality Assurance**

- Self-monitoring
- Constitutional compliance
- Truth in advertising
- Continuous validation

### 10. 🧪 **Testing & Quality**

#### **Test Suite**

- **100+ tests** covering all major components
- Unit tests for individual modules
- Integration tests for workflows
- End-to-end tests for complete scenarios
- Invariant tests for system properties
- Performance benchmarks

#### **Code Quality**

- Type hints throughout
- Comprehensive docstrings
- Constitutional compliance validation
- Automated testing via CI/CD

### 11. ⚡ **Performance Features**

- **Parallel processing** — Multi-threaded search and pattern scanning
- **ripgrep integration** — Uses fastest search tool when available
- **Smart caching** — Caches observations for faster re-analysis
- **Lazy loading** — Heavy dependencies loaded only when needed
- **Resource limits** — Configurable memory and CPU limits

---

## 🎯 Use Cases

### For Individual Developers

- **Onboarding** — Understand new codebases in days, not weeks
- **Code Reviews** — Check for architectural violations before commit
- **Refactoring** — Map dependencies before making changes
- **Learning** — Understand how complex systems work

### For Teams

- **Knowledge Sharing** — Preserve investigation trails for team
- **Code Reviews** — Automated constitutional violation detection
- **Documentation** — Generate up-to-date architecture docs
- **Onboarding** — Help new team members understand the system

### For Organizations

- **Architecture Reviews** — Enforce architectural standards
- **Security Audits** — Detect hardcoded secrets automatically
- **Compliance** — Document code structure for audits
- **Legacy Modernization** — Understand before refactoring

---

## 🌟 What Makes CodeMarshal Different?

| Traditional Tools          | CodeMarshal                 |
| -------------------------- | --------------------------- |
| ❌ AI hallucinations       | ✅ Only shows what exists   |
| ❌ Overwhelming dashboards | ✅ One question at a time   |
| ❌ Hidden assumptions      | ✅ Declared limitations     |
| ❌ Generic patterns        | ✅ Constitutional awareness |
| ❌ Passive consumption     | ✅ Active investigation     |
| ❌ Transient analysis      | ✅ Immutable evidence       |

---

## 📋 Feature Summary by Version

### v2.0 (Current) ✅

- [x] Configuration management commands
- [x] Backup & restore system
- [x] Code search with ripgrep
- [x] Pattern detection (8 security patterns)
- [x] Custom pattern support
- [x] Cleanup & repair commands
- [x] Built-in test runner
- [x] HTML export format
- [x] CSV export format
- [x] Docker support (prod & dev)
- [x] Pre-commit hooks
- [x] GitHub Actions workflow
- [x] 100+ comprehensive tests
- [x] Memory monitoring interface

### Coming in v2.1

- [ ] Jupyter Notebook export
- [ ] Plugin system
- [ ] Desktop GUI
- [ ] Performance patterns
- [ ] Style patterns
- [ ] More IDE integrations

### Future (v3.0)

- [ ] Knowledge base integration
- [ ] Machine learning patterns (with human verification)
- [ ] Multi-language support expansion
- [ ] Distributed analysis
- [ ] Real-time collaboration

---

## 🚀 Getting Started

```bash
# Install
pip install codemarshal

# Or clone and install locally
git clone https://github.com/d4rkbl4de/CodeMarshal
cd CodeMarshal
pip install -e .

# Verify installation
codemarshal --version

# Analyze your first project
codemarshal investigate /path/to/your/project

# Or use the TUI for interactive exploration
codemarshal tui
```

---

## 📚 Documentation

- **README.md** — Quick start and overview
- **docs/USER_GUIDE.md** — Detailed usage guide
- **docs/API_DOCUMENTATION.md** — API reference
- **docs/INTEGRATION_EXAMPLES.md** — Integration examples
- **architecture.md** — System architecture
- **Structure.md** — Directory structure
- **CONSTITUTIONAL_ANALYSIS.md** — 24 constitutional articles

---

## 💡 Pro Tips

1. **Start with `observe`** — Collect observations before investigating
2. **Use `--dry-run`** — Preview cleanup operations before executing
3. **Export regularly** — Save investigation state with `codemarshal backup create`
4. **Add custom patterns** — Define patterns specific to your codebase
5. **Use TUI for exploration** — Interactive mode for deep dives
6. **Check with `--info`** — System diagnostics to troubleshoot issues

---

**CodeMarshal v2.0** — Truth-preserving investigation for complex codebases.

_Because understanding your code shouldn't require holding it all in your head._
